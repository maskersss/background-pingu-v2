import re, random, traceback
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown import markdown
from loghelper import parser
from loghelper.issues.checker import IssueChecker
from loghelper.config import *

def get_logs_from_link(link, include_content=False):
    matches = re.findall(LINK_PATTERN, link)
    if len(matches) > 3:
        matches = random.sample(matches, 3)

    logs = [(match.split("?ex")[0], parser.Log.from_link(match)) for match in matches]
    logs = [(link, log) for (link, log) in logs if log is not None]
    logs = sorted(logs, key=lambda x: len(x[1]._content), reverse=True)

    if include_content:
        logs.append(("message", parser.Log(link)))

    return logs

def get_settings(log_link, include_content=False):
    logs = get_logs_from_link(log_link, include_content=include_content)
    for link, log in logs:
        try:
            reply, success = IssueChecker(
                log, link, None, None, "web"
            ).seedqueue_settings()
            if success:
                return reply
        except Exception as e:
            error = "".join(traceback.format_exception(e))
            return f"Error:\n{error}"
    return None


app = FastAPI(root_path="/sq-settings")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyse", response_class=HTMLResponse)
async def analyse(request: Request, loglink: str = Form(...)):
    raw_result = get_settings(loglink, include_content=True) or "Couldn't get settings."
    html_result = markdown(raw_result, extensions=['nl2br', 'fenced_code'])\
        .replace("<pre><code>", '<pre class="language-none" data-prismjs-copy="Copy the Java arguments!"><code>')
    return templates.TemplateResponse("_result.html", {
        "request": request,
        "result": html_result
    })
