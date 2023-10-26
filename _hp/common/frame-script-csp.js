var urlParams = new URLSearchParams(decodeURIComponent(window.location.search));
var id = urlParams.get("count");
let response_id = urlParams.get("resp_id");
window.parent.postMessage({ "id": id, "message": "message send" }, "*");