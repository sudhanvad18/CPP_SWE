import json
import html
import gradio as gr

# ------------------------
# Load data
# ------------------------
with open("faculty.json", "r", encoding="utf-8") as f:
    FACULTY = json.load(f)

def get_faculty_by_name(name):
    for f in FACULTY:
        if f["name"].strip().lower() == name.strip().lower():
            return f
    return None

def faculty_to_html(f):
    name = html.escape(f.get("name", ""))
    title = html.escape(f.get("title", "") or "")
    email = html.escape(f.get("email", "") or "")
    research = html.escape(f.get("research", "") or "Not listed")
    website = f.get("website", "") or f.get("profile_link", "#")
    website_html = f'<a href="{html.escape(website)}" target="_blank" rel="noopener">{html.escape(website)}</a>'

    html_content = f"""
    <div style="padding:0.5rem 0">
        <h3>{name}</h3>
        {'<div><strong>' + title + '</strong></div>' if title else ''}
        {'<div>E-mail: <a href="mailto:' + email + '">' + email + '</a></div>' if email else ''}
        <div>Website: {website_html}</div>
        <h4 style="margin-top:1em;">Research Interests</h4>
        <div>{research}</div>
    </div>
    """
    return html_content

# ------------------------
# Logic
# ------------------------
def on_search(query):
    query = (query or "").strip()
    if not query:
        return (
            "<div>Please enter a partial or full faculty name.</div>",
            gr.update(choices=[], value=None, visible=False),
        )

    q = query.lower()
    matches = [f["name"] for f in FACULTY if q in f["name"].lower()]

    if not matches:
        return (
            f"<div>❌ No matches found for <em>{html.escape(query)}</em>.</div>",
            gr.update(choices=[], value=None, visible=False),
        )

    if len(matches) == 1:
        f = get_faculty_by_name(matches[0])
        return faculty_to_html(f), gr.update(choices=[], value=None, visible=False)

    msg = (
        f"<div>🔎 Found {len(matches)} matches for "
        f"<strong>{html.escape(query)}</strong>. Select one from the list below:</div>"
    )
    return msg, gr.update(choices=matches, value=None, visible=True)

def on_select(selected_name):
    if not selected_name or selected_name.strip() == "":
        return gr.update(), gr.update()
    f = get_faculty_by_name(selected_name)
    if not f:
        return (
            f"<div>❌ Could not find data for <em>{html.escape(selected_name)}</em>.</div>",
            gr.update(),
        )
    return faculty_to_html(f), gr.update(visible=True)

# ------------------------
# UI
# ------------------------
with gr.Blocks(title="Purdue ECE Faculty Finder") as demo:
    gr.Markdown("# 🔍 Purdue ECE Faculty Finder")
    gr.Markdown(
        "Enter a partial or full faculty name. If multiple matches are found, "
        "select one from the dropdown below. Click a personal website to open it in a new tab."
    )

    with gr.Row():
        name_input = gr.Textbox(label="Faculty Name", placeholder="e.g., David Love")
        search_btn = gr.Button("Search", variant="primary")

    output = gr.HTML()
    dropdown = gr.Dropdown(
        label="Matching Faculty",
        choices=[],
        interactive=True,
        visible=False,
    )

    search_btn.click(on_search, inputs=name_input, outputs=[output, dropdown])
    name_input.submit(on_search, inputs=name_input, outputs=[output, dropdown])
    dropdown.change(on_select, inputs=dropdown, outputs=[output, dropdown])

# ------------------------
# Launch (no footer, no “use API” links)
# ------------------------
if __name__ == "__main__":
    demo.launch(show_api=False, show_footer=False)
