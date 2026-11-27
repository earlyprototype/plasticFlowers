"""Check portrait reload and PNG download against a local frontend and an offline API fixture."""

from pathlib import Path
import re

from playwright.sync_api import expect, sync_playwright


def main():
    records = {
        key: {"id": key, "name": name, "created_at": "2026-01-01T09:00:00Z", "ended_at": None}
        for key, name in (("plate-a", "Garden"), ("legacy", "Old garden"))
    }

    def session_api(route):
        path = route.request.url.partition("/api/sessions")[2]
        if path == "":
            body = {"sessions": list(records.values())}
        else:
            key, _, resource = path.strip("/").partition("/")
            if route.request.method == "PATCH":
                records[key].update(route.request.post_data_json)
            if resource == "graph":
                body = {"nodes": [], "relationships": [], "flowers": [], "bridges": []}
            elif resource == "references":
                body = {"references": []}
            elif resource == "stream":
                return route.fulfill(content_type="text/event-stream", body=": heartbeat\n\n")
            else:
                body = {**records[key], "transcript": ""}
        route.fulfill(json=body)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page()
        page.route("**/api/sessions**", session_api)
        # Observe the headline painted into the visible layer and into the canvas
        # actually passed to the PNG encoder. Both methods still draw normally.
        page.add_init_script("""
            const headlines = new WeakMap();
            const expected = new Set(["Glasshouse notes", "Session legacy"]);
            const draw = CanvasRenderingContext2D.prototype.fillText;
            CanvasRenderingContext2D.prototype.fillText = function(text, x, y, ...rest) {
              if (expected.has(text)) {
                headlines.set(this.canvas, text);
                if (this.canvas.isConnected) window.liveHeadline = text;
              }
              return draw.call(this, text, x, y, ...rest);
            };
            const encode = HTMLCanvasElement.prototype.toBlob;
            HTMLCanvasElement.prototype.toBlob = function(...args) {
              if (headlines.has(this)) window.encodedHeadline = headlines.get(this);
              return encode.apply(this, args);
            };
        """)
        page.goto("http://127.0.0.1:3000/")
        editor = page.get_by_role("textbox", name="Portrait title")

        def open_garden():
            page.get_by_role("button", name=re.compile("Load")).click()
            page.get_by_text("Garden", exact=True).first.click()
            expect(page.get_by_text("Session Name", exact=True)).to_be_visible()
            page.locator("#portrait-toggle").click()

        def check_png(headline):
            page.wait_for_function("value => window.liveHeadline === value", arg=headline)
            with page.expect_download() as event:
                page.locator("#save-portrait").click()
            assert page.evaluate("window.encodedHeadline") == headline
            with Path(event.value.path()).open("rb") as png:
                assert png.read(8) == bytes.fromhex("89504e470d0a1a0a")
            print(f"Canvas and downloaded PNG passed for {headline!r}")

        open_garden()
        editor.fill("Glasshouse notes")
        with page.expect_response(lambda r: r.request.method == "PATCH" and r.status == 200):
            page.get_by_role("button", name="Save title").click()
        page.reload()
        open_garden()
        expect(editor).to_have_value("Glasshouse notes")
        check_png("Glasshouse notes")

        page.reload()
        entry = page.get_by_role("textbox", name="Session ID")
        entry.fill("legacy")
        entry.press("Enter")
        expect(page.get_by_text("Old garden", exact=True)).to_be_visible()
        page.locator("#portrait-toggle").click()
        expect(editor).to_have_value("")
        check_png("Session legacy")
        browser.close()


if __name__ == "__main__":
    main()
