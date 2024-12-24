from .start import start_routine
from .entities import ExitReason, RoutineEntry


# def resume_fuzz(routine: RoutineEntry) -> bool:
#     logger.info(f"Resuming execution of routine {routine.get_name()}")
#     flag = start_routine(routine)
#     if not flag:
#         logger.error(f"Failed to resume routine {routine.get_name()}")
#     return flag
#
#
# def try_resume(routine: RoutineEntry) -> bool:
#     reason = check_exit_reason(routine)
#     if reason == ExitReason.OTHER:
#         return False
#
#     return resume_fuzz(routine)
