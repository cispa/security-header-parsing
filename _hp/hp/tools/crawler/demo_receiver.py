from multiprocessing import Pool
import psycopg
import json

# Setup the config
try:
	proj_config = json.load(open("config.json"))
except OSError:
	try:
		proj_config = json.load(open("_hp/hp/tools/config.json"))
	except OSError:
		proj_config = json.load(open("../config.json"))

DB_URL = proj_config['DB_URL'].replace("postgresql+psycopg2://", "postgresql://")


def run_function(run_id):
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("LISTEN page_runner")
        gen = conn.notifies()

        # Start long running test runner page
        # send_intent(...)

        for notify in gen:
            if notify.payload == run_id:
                print(notify)
                gen.close()
    

if __name__ == "__main__":
    with Pool(5) as p:
        p.map(run_function, ["unknown", "unknown", "unknown", "unknown", "random"])