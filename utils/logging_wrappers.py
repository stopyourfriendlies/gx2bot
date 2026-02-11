# GET RID OF THIS FILE
# JUST TO SIMPLIFY REPEATED LOGGING MESSAGES ACROSS EVERYTHING
import logging  # to log obviously

logger = logging.getLogger("Volunteer")  # set up a log called 'TO'
logger.setLevel(
    logging.DEBUG
)  # set Logging Level (DEBUG, INFO, WARNING, ERROR, CRITICAL) to only show info level and up

# output log to file
handler = logging.FileHandler(
    filename="VolunteerCommands.log", encoding="utf-8", mode="w"
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)  # change this if you want log items formatted differently
logger.addHandler(handler)


def log_shift_init_fired(shift_type):
    logger.info(f"{shift_type} Select __init__ fired.")


def log_available_shifts(shift_type, options):
    logger.info(
        f"Shifts that are available (Shift Type: {shift_type}): {[getattr(x, "label") for x in options]}"
    )


def log_queue_request(requester, shift_type, shift_day, shift_time):
    logger.info(
        f"Queue request: {requester} is requesting {shift_type.upper()} at {shift_day.title()} {shift_time}"
    )


def log_queue_size(requests_queue):
    logger.info("Queue size: " + str(requests_queue.qsize()))


# log_shift_init_fired(shift_type)
# log_available_shifts(shift_type, options)
# log_queue_request(requester, shift_type, shift_day, shift_time)
# log_queue_size(requests_queue)
