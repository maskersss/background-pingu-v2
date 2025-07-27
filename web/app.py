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

def check_log(log_link, include_content=False):
    result = {"text": None, "embed": None}
    logs = get_logs_from_link(log_link, include_content)
    
    for link, log in logs:
        try:
            results = IssueChecker(
                log,
                link,
                None,  # No guild ID
                None,  # No channel ID
                "web",
            ).check()
            
            if results.has_values():
                messages = results.build()
                result["embed"] = "\n".join(messages)
                return result
        except Exception as e:
            error = "".join(traceback.format_exception(e))
            result["text"] = f"Error:\n{error}"
            return result
    return result


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyse", response_class=HTMLResponse)
async def analyse(request: Request, loglink: str = Form(...)):
    raw_result = check_log(loglink, include_content=True) or "Couldn't get log feedback."
    parts = []
    if raw_result.get("text"):
        parts.append(raw_result["text"])
    if raw_result.get("embed"):
        parts.append(raw_result["embed"])
    
    html_result = "\n".join(parts)
    html_result = markdown(html_result, extensions=['nl2br', 'fenced_code'])
    return templates.TemplateResponse("_result.html", {
        "request": request,
        "result": html_result
    })
