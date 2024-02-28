from wptserve.handlers import json_handler
import psycopg
import json

# Setup the config
try:
    proj_config = json.load(open("config.json"))
except OSError:
    try:
        proj_config = json.load(open("_hp/tools/config.json"))
    except OSError:
        proj_config = json.load(open("../config.json"))

DB_URL = proj_config['DB_URL'].replace("postgresql+psycopg2://", "postgresql://")


@json_handler
def main(request, response):
    run_id = request.GET.get("run_id", "unknown")
    sql = "SELECT pg_notify(%s, %s);"
    try:
        with psycopg.connect(DB_URL, autocommit=True) as conn:
                conn.execute(sql, ("page_runner", run_id,))
    except psycopg.Error as e:
        print("Error notifying page runner:", e)
        return {"result": str(e)}
    
    return {"result": "done"}
