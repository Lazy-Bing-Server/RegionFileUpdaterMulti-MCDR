import copy
import sys
import threading
from typing import TYPE_CHECKING, Dict, Optional, Callable, Any, Union

from mcdreforged.api.all import *

from region_file_updater_multi.region_upstream_manager import Region
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.base import BaseTrigger
from region_file_updater_multi.utils.misc_tools import (
    get_scheduler,
    named_thread,
    get_player_from_src,
)
from region_file_updater_multi.utils.units import Duration
from region_file_updater_multi.components.misc import get_rfum_comp_prefix

if TYPE_CHECKING:
    from region_file_updater_multi.rfum import RegionFileUpdaterMulti


class UpdateSession:
    def __init__(self, rfum: "RegionFileUpdaterMulti"):
        self.__region_list_lock = threading.RLock()
        self.__session_pending_lock = threading.Lock()
        self.__regions: Dict[Region, Optional[str]] = {}
        self.__rfum = rfum
        self.__scheduler_lock = threading.RLock()
        self.__scheduler = get_scheduler(BlockingScheduler)
        self.__waiting = False
        self.__aborted = True
        self.__started_lock = threading.Lock()
        self.__cached_countdown = 0

    def reset_countdown(self):
        self.__cached_countdown = round(
            self.__rfum.config.update_operation.update_delay.value
        )

    @property
    def started(self):
        return self.__started_lock.locked()

    @property
    def waiting(self):
        return self.__waiting

    @property
    def pending_lock(self):
        return self.__session_pending_lock

    @property
    def is_session_running(self):
        return self.__session_pending_lock.locked()

    def get_current_regions(self, deepcopy: bool = False):
        return copy.deepcopy(self.__regions) if deepcopy else self.__regions.copy()

    def assert_allowed(self):
        if self.is_session_running:
            raise RuntimeError("Modifying is not allowed at this time")

    def add_region(self, region: Region, player: Optional[str]):
        self.assert_allowed()
        with self.__region_list_lock:
            if region in self.__regions.keys():
                raise ValueError(f"{repr(region)} already exists")
            self.__regions[region] = player
            self.__rfum.verbose(f"{player or 'Console'} added region {str(region)}")

    def remove_region(self, region: Region, player: Optional[str]):
        self.assert_allowed()
        with self.__region_list_lock:
            if region not in self.__regions.keys():
                raise ValueError(f"{repr(region)} not found in current session")
            del self.__regions[region]
            self.__rfum.verbose(f"{player or 'Console'} removed region {str(region)}")

    def remove_all_regions(self):
        self.assert_allowed()
        self.__remove_all_regions()

    def __remove_all_regions(self):
        with self.__region_list_lock:
            self.__regions = {}
            self.__rfum.verbose("Removed all the regions from session")

    @named_thread
    def scheduler_stop(self, *args, **kwargs):
        if self.__scheduler.running:
            self.__scheduler.shutdown()
        self.scheduler_remove_all_jobs()
        self.__rfum.verbose("Scheduler terminated")

    def scheduler_remove_all_jobs(self):
        with self.__scheduler_lock:
            self.__scheduler.remove_all_jobs()
            self.__rfum.verbose("Removed all the jobs from scheduler")

    def scheduler_start(self):
        self.__scheduler.start()
        self.__rfum.verbose("Started scheduler")

    def scheduler_add_job(self, func: Callable[[], Any], trigger: BaseTrigger):
        with self.__scheduler_lock:
            return self.__scheduler.add_job(func, trigger)

    def confirm_session(self):
        with self.__scheduler_lock:
            self.reset_countdown()
            self.__aborted = False
            if self.__cached_countdown <= 0 and self.__scheduler.running:
                self.scheduler_stop()
            else:
                self.scheduler_remove_all_jobs()
                self.scheduler_add_job(
                    self.countdown, trigger=IntervalTrigger(seconds=1)
                )
            self.__rfum.server.broadcast(
                get_rfum_comp_prefix(self.__rfum.rtr("session.task_confirmed"))
            )
            self.countdown()

    def countdown(self):
        rfum = self.__rfum
        server = rfum.server
        self.__cached_countdown -= 1
        if not self.__cached_countdown > 0 and self.__scheduler.running:
            return self.scheduler_stop()
        server.broadcast(
            get_rfum_comp_prefix(
                rfum.rtr(
                    "session.countdown",
                    sec=str(self.__cached_countdown),
                    region_count=len(self.__regions),
                )
            )
        )

    def abort_session(self):
        with self.__scheduler_lock:
            self.__aborted = True
            self.scheduler_stop()

    def run_session(
        self,
        source: CommandSource,
        requires_confirm: bool = True,
        confirm_time_wait: Optional[Duration] = None,
    ):
        confirm_time_wait_value: Union[int, float] = (
            confirm_time_wait or self.__rfum.config.update_operation.confirm_time_wait
        ).value

        server = self.__rfum.server
        history = self.__rfum.history
        region_upstream_manager = self.__rfum.region_upstream_manager

        # Session time out
        def timed_out_handler():
            with self.__scheduler_lock:
                self.scheduler_stop()
                server.broadcast()

        acq = self.__session_pending_lock.acquire(blocking=False)
        if not acq:
            raise RuntimeError("Session already exists")
        try:
            # Wait confirm & countdown
            if requires_confirm:
                self.scheduler_add_job(
                    timed_out_handler,
                    trigger=IntervalTrigger(seconds=confirm_time_wait_value),
                )
            else:
                self.confirm_session()
            if requires_confirm or self.__cached_countdown > 0:
                self.scheduler_start()

            if self.__aborted:
                self.__rfum.server.broadcast(
                    get_rfum_comp_prefix(self.__rfum.rtr("session.task_aborted"))
                )
                return
            # Stop server
            server.stop()
            server.wait_until_stop()

            self.__rfum.file_utilities.__enter__()
            # Run update
            with self.__region_list_lock:
                region_list = self.__regions
                self.__regions = {}
                try:
                    self.__started_lock.acquire(blocking=True)
                    for region in region_list.keys():
                        region_upstream_manager.extract_region_files(region)
                finally:
                    history.record(
                        get_player_from_src(source),
                        sys.exc_info()[0] is None,
                        {str(region): player for region, player in region_list.items()},
                        self.__rfum.region_upstream_manager.get_current_upstream().name,
                    )
                    if self.__started_lock.locked():
                        self.__started_lock.release()

            # Start server
            server.start()

        except Exception as exc:
            self.__rfum.logger.exception("Error running update session")
            self.__rfum.verbose("Restoring files")
            self.__rfum.file_utilities.restore_all()
            if server.is_server_startup():
                server.say(self.__rfum.rtr("session.error_occurred", str(exc)))
            if not server.is_server_running():
                server.start()
        finally:
            if self.started:
                self.__started_lock.release()
            if acq:
                self.__session_pending_lock.release()
            self.__waiting = False
            self.__aborted = True
            self.__scheduler = get_scheduler(BlockingScheduler)
            self.__rfum.file_utilities.__exit__(*sys.exc_info())

    def register_event_listeners(self):
        self.__rfum.server.register_event_listener(
            MCDRPluginEvents.PLUGIN_UNLOADED, self.scheduler_stop
        )
