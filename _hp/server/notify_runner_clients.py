from wptserve.handlers import json_handler
import psycopg
import json

# Setup the config
proj_config = json.load(open("_hp/hp/tools/config.json"))
DB_URL = proj_config['DB_URL'].replace("postgresql+psycopg2://", "postgresql://")

@json_handler
def main(request, response):
    """Notify runner clients via postgres pg_notify that their run is doen.

    Args:
        request: GET request with run_id
        response: Response to be generated

    Returns:
        JSON: returns {"result": "done"} or the postgres error
    """
    run_id = request.GET.get("run_id", "unknown")
    sql = "SELECT pg_notify(%s, %s);"
    try:
        with psycopg.connect(DB_URL, autocommit=True) as conn:
                conn.execute(sql, ("page_runner", run_id,))
    except psycopg.Error as e:
        print("Error notifying page runner:", e)
        return {"result": str(e)}

    return {"result": "done"}
