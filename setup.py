import schedule
import time
import retirve_data_power_cut


def scheduled_job_power():
    print(time.ctime(), flush=True)
    print("Job is running", flush=True)
    retirve_data_power_cut.EventHandle().create_event()


schedule.every().day.at("06:00").do(scheduled_job_power)

while True:
    print(time.ctime(), flush=True)
    schedule.run_pending()
