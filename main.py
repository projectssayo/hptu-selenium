import json
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from playwright.async_api import async_playwright
import sys
import os

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

home = "https://results.indiaresults.com/hp/himtu/hp-himtu/mquery.aspx?id=1800266513"

app = FastAPI()

async def data_extraction(page, roll):
    await page.goto(home)

    roll_input = page.locator("input[placeholder='ROLL NO']")
    await roll_input.wait_for(state="visible", timeout=8000)
    await roll_input.fill(str(roll))
    await roll_input.press("Enter")

    await page.wait_for_url(lambda url: url != home, timeout=10000)

    info = await page.evaluate("""() => {
        let a = {};
        for (let i = 0; i < 3; i++) {
            let parts = document
                .getElementsByClassName("table table-bordered")[1]
                .childNodes[1]
                .children[2]
                .querySelector("td")
                .childNodes[2]
                .getElementsByTagName("tr")[i]
                .innerText.split("\\t");

            let key = parts[0].trim().toLowerCase().replace(/ /g, "_").replace(/\\./g, "").replace(/'s/g, "");
            let val = parts[1]?.trim();

            a[key] = val;
        }
        return a;
    }""")


    print(info)

    marks = await page.evaluate("""() => {
        let x = [];
        let rows = document
            .getElementsByClassName("table table-bordered")[1]
            .childNodes[1]
            .children[2]
            .querySelector("td")
            .childNodes[4]
            .getElementsByTagName("tbody")[0]
            .children;

        for (let i = 1; i < rows.length - 1; i++) {
            let data = rows[i].innerText.split("\\t");
            x.push({
                subject: data[0]?.trim(),
                subject_code: data[1]?.trim(),
                credit: data[2]?.trim(),
                grade: data[3]?.trim()
            });
        }
        return x;
    }""")

    print(marks)

    result = await page.evaluate("""() => {
        let arr = [];
        for (let i = 0; i < 3; i++) {
            let row = document
                .getElementsByClassName("table table-bordered")[1]
                .childNodes[1]
                .children[2]
                .querySelector("td")
                .childNodes[5]
                .getElementsByTagName("tbody")[0]
                .children[i];

            let parts = row.innerText.split("\\t");
            arr.push({ [parts[0].trim().toLowerCase().replace(/ /g, "_").replace(/\\./g, "")]: parts[1]?.trim() });
        }
        return arr;
    }""")

    print(result)

    return {
        "roll": roll,
        "personal_info": info,
        "marks": marks,
        "result": result
    }

async def stream_results(rolls):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for roll in rolls:
            try:
                data = await data_extraction(page, roll)
                yield f"data: {json.dumps(data)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'roll': roll, 'error': str(e)})}\n\n"

            await asyncio.sleep(0)

        await browser.close()

@app.get("/")
async def root():
    return {"message": "Server is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/info")
async def info():
    example_rolls = [240603010065, 240603010066, 240603010067, 240603010068, 240603010069, 
                    240603010070, 240603010071, 240603010072, 240603010073, 240603010074,
                    240603010075, 240603010076, 240603010077, 240603010078, 240603010079,
                    240603010080, 240603010081, 240603010082, 240603010083, 240603010084,
                    240603010085, 240603010086, 240603010087, 240603010088, 240603010089,
                    240603010090, 240603010091, 240603010092, 240603010093, 240603010094,
                    240603010095, 240603010096, 240603010097, 240603010098, 240603010099,
                    240603010100]
    
    # For local development, you can use localhost
    base_url = "http://127.0.0.1:8000"
    
    # For production, you can get the actual URL if needed
    # But for the example, we'll use localhost as requested
    example_url = f"{base_url}/results/stream?rolls={json.dumps(example_rolls)}"
    
    return {
        "info": example_url,
        "usage": "Send a GET request to /results/stream with a 'rolls' parameter containing a JSON array of roll numbers",
        "example_rolls": example_rolls,
        "note": "The response is a Server-Sent Events (SSE) stream. Use EventSource in JavaScript or appropriate SSE client to receive data."
    }

@app.get("/results/stream")
async def stream_api(rolls: str):
    rolls = json.loads(rolls)
    return StreamingResponse(stream_results(rolls), media_type="text/event-stream")
