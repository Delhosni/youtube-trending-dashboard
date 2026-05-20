import textwrap
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, ctx

# ══════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════
country_stats    = pd.read_csv("data/processed/country_stats.csv")
top_cats_country = pd.read_csv("data/processed/top_categories_full.csv")
day_hour_data    = pd.read_csv("data/processed/day_hour_heatmap.csv")
clean_df         = pd.read_csv("data/processed/youtube_trending_clean.csv")
top_ch_category  = pd.read_csv("data/processed/top_channels_category.csv")
scatter_df       = pd.read_csv("data/processed/scatterplot_data.csv")
channel_content  = pd.read_csv("data/processed/channel_content_mix.csv")

for _df in [country_stats, top_cats_country, day_hour_data,clean_df,top_ch_category,scatter_df,channel_content]:
    _df.columns = _df.columns.str.strip()

scatter_df["is_viral"] = scatter_df["is_viral"].astype(bool)

# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════
DAY_ORDER = ["Monday","Tuesday","Wednesday",
             "Thursday","Friday","Saturday","Sunday"]

COUNTRY_ISO = {
    "Brazil":"BRA","Canada":"CAN","Germany":"DEU",
    "France":"FRA","United Kingdom":"GBR","India":"IND",
    "Japan":"JPN","South Korea":"KOR","Mexico":"MEX",
    "Russia":"RUS","United States":"USA",
}
ISO_COUNTRY = {v: k for k, v in COUNTRY_ISO.items()}

# Qualitative palette — no red, colorblind-safe
# Reference: ColorBrewer 2.0
CATEGORY_COLORS = {
    "Gaming":                "#1f77b4",  # steel blue
    "Music":                 "#c5b0d5",  # light purple
    "Entertainment":         "#2ca02c",  # green
    "People & Blogs":        "#9467bd",  # purple
    "Film & Animation":      "#8c564b",  # brown
    "Howto & Style":         "#e377c2",  # pink
    "Sports":                "#7f7f7f",  # grey
    "Pets & Animals":        "#bcbd22",  # yellow-green
    "Science & Technology":  "#17becf",  # teal
    "Comedy":                "#aec7e8",  # light blue
    "Travel & Events":       "#ffbb78",  # light orange
    "News & Politics":       "#98df8a",  # light green
    "Education":             "#ff7f0e",  # orange
    "Nonprofits & Activism": "#f0a500",  # amber
    "Autos & Vehicles":      "#5ba4cf",  # sky blue
    "Unknown":               "#AAAAAA",  # grey 
}

DEFAULT = "United States"
H_TOP   = 300   # top row height (map + categories)
H_BOT   = 260   # bottom row height (heatmap + scatter + trending)

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def get_country(click_data):
    if not click_data:
        return None
    try:
        p   = click_data["points"][0]
        iso = p.get("location")
        if iso and iso in ISO_COUNTRY:
            return ISO_COUNTRY[iso]
        cd = p.get("customdata")
        if cd and str(cd[0]) in COUNTRY_ISO:
            return str(cd[0])
    except Exception:
        pass
    return None


def fig_map(selected=None):
    df = country_stats.copy()
    df["iso"] = df["country_name"].map(COUNTRY_ISO)
    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        locations=df["iso"], z=df["avg_views"],
        customdata=df[["country_name","avg_views",
                       "avg_engagement","viral_count",
                       "total_videos"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Avg Views: %{customdata[1]:,.0f}<br>"
            "Avg Engagement: %{customdata[2]:.2f}%<br>"
            "Viral Videos: %{customdata[3]:,.0f}<br>"
            "<extra></extra>"
        ),
        colorscale="Viridis_r",
        colorbar=dict(
            title=dict(text="Avg Views", font=dict(size=8)),
            thickness=9, len=0.5, tickfont=dict(size=7),
        ),
        marker=dict(line=dict(color="white", width=0.7)),
        zmin=df["avg_views"].min(),
        zmax=df["avg_views"].max(),
    ))
    if selected and selected in COUNTRY_ISO:
        fig.add_trace(go.Choropleth(
            locations=[COUNTRY_ISO[selected]], z=[1],
            colorscale=[[0,"rgba(255,215,0,0.8)"],
                        [1,"rgba(255,215,0,0.8)"]],
            showscale=False, hoverinfo="skip",
            marker=dict(line=dict(color="gold", width=2.5)),
        ))
    fig.update_layout(
        autosize=False, height=H_TOP,
        geo=dict(
            showframe=False, showcoastlines=True,
            coastlinecolor="#bbb", showland=True,
            landcolor="#d5d5d5", showocean=True,
            oceancolor="#cfe2f3", showlakes=True,
            lakecolor="#cfe2f3",
            projection_type="natural earth",
            bgcolor="white",
            domain=dict(x=[0, 1], y=[0, 1]),
        ),
        margin=dict(l=0, r=0, t=0, b=18),
        geo_projection_scale=1.2,
        paper_bgcolor="white",
        font=dict(family="Segoe UI", size=9),
        annotations=[dict(
            text="🟡 Covered (11)   ⬜ Not in dataset",
            x=0.5, y=-0.04, xref="paper", yref="paper",
            showarrow=False, font=dict(size=8, color="#888"),
        )],
    )
    return fig


def fig_categories(country):
    df  = top_cats_country[
        top_cats_country["country_name"] == country
    ].copy()
    val = "avg_views" if "avg_views" in df.columns else "total_views"
    eng = "avg_engagement" if "avg_engagement" in df.columns else None
    df  = df.sort_values(val, ascending=True)
    kw  = dict(color=eng, color_continuous_scale="Blues") if eng else {}
    fig = px.bar(
        df, x=val, y="category_name", orientation="h", **kw,
        labels={val:"Views","category_name":"Category",
                **({"avg_engagement":"Eng%"} if eng else {})},
    )
    if eng:
        fig.update_layout(
            coloraxis_colorbar=dict(
                title=dict(text="Eng%", font=dict(size=8)),
                thickness=8, tickfont=dict(size=7),
            )
        )
    fig.update_layout(
        autosize=False, height=H_TOP,
        margin=dict(l=4, r=4, t=4, b=4),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Segoe UI", size=10),
        xaxis=dict(title="Views", gridcolor="#ececec",
                   tickformat=".2s"),
        yaxis=dict(title=""),
    )
    return fig


def fig_heatmap(country, metric):
    df = day_hour_data[
        day_hour_data["country_name"] == country
    ].copy()
    pivot = df.pivot_table(
        index="publish_day_name", columns="publish_hour",
        values=metric, aggfunc="mean",
    ).fillna(0)
    pivot = pivot.reindex([d for d in DAY_ORDER if d in pivot.index])
    lbl = {"avg_views":"Avg Views",
           "avg_engagement":"Avg Engagement %",
           "total_videos":"Total Videos"}.get(metric, metric)
    hover = []
    for day in pivot.index:
        row = []
        for hour in pivot.columns:
            val  = pivot.loc[day, hour]
            vids = df[(df["publish_day_name"]==day) &
                      (df["publish_hour"]==hour)
                     ]["total_videos"].sum()
            row.append(
                f"<b>{day} at {int(hour):02d}:00</b><br>"
                f"{lbl}: {val:,.0f}<br>"
                f"Videos: {int(vids)}"
            )
        hover.append(row)
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[f"{int(h):02d}:00" for h in pivot.columns],
        y=list(pivot.index),
        text=hover, hovertemplate="%{text}<extra></extra>",
        colorscale="Blues",
        showscale=False,
    ))
    fig.update_layout(
        autosize=False, height=H_BOT,
        title=dict(
            text=f"Darker = More {lbl} — {country}",
            font=dict(size=9), x=0.5, y=0.99,
        ),
        xaxis=dict(title="Hour (UTC)", tickmode="linear",
                   dtick=2, tickfont=dict(size=7),
                   tickangle=-45),
        yaxis=dict(title="", tickfont=dict(size=9)),
        margin=dict(l=90, r=10, t=25, b=70),
        paper_bgcolor="white",
        font=dict(family="Segoe UI"),
    )
    return fig


def fig_channels_for_category(category):
    df = top_ch_category[
        top_ch_category["category_name"] == category
    ].copy()
    val = "total_views" if "total_views" in df.columns else "avg_views"
    df  = df.sort_values(val, ascending=True).tail(15)
    color = CATEGORY_COLORS.get(category, "#4361EE")
    fig = px.bar(
        df, x=val, y="channel_title", orientation="h",
        color_discrete_sequence=[color],
        hover_data={val:":,.0f","total_videos":":,"},
        labels={val:"Total Views","channel_title":"Channel"},
    )
    fig.update_layout(
        autosize=False, height=H_BOT,
        margin=dict(l=4, r=4, t=4, b=4),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Segoe UI", size=10),
        showlegend=False,
        xaxis=dict(title="Total Views", gridcolor="#ececec",
                   tickformat=".2s"),
        yaxis=dict(title=""),
    )
    return fig

def fig_donut(channel):
    """Donut chart: distribution of views by country for a channel."""
    df = clean_df[
        clean_df["channel_title"] == channel
    ].copy()

    if df.empty:
        return go.Figure(layout=dict(
            height=H_BOT, paper_bgcolor="white",
            annotations=[dict(text="No data", x=0.5, y=0.5,
                            showarrow=False, font=dict(size=14))]
        ))

    # Aggregate total views per country
    country_views = (
        df.groupby("country_name")["views"]
        .sum()
        .reset_index()
        .sort_values("views", ascending=False)
    )

    # Country colours (distinct from category colours)
    COUNTRY_COLORS = [
        "#1f77b4","#ff7f0e","#2ca02c","#9467bd","#8c564b",
        "#e377c2","#7f7f7f","#bcbd22","#17becf","#aec7e8","#ffbb78"
    ]

    short = channel[:18] + "…" if len(channel) > 18 else channel

    fig = go.Figure(go.Pie(
        labels=country_views["country_name"],
        values=country_views["views"],
        hole=0.5,
        marker=dict(colors=COUNTRY_COLORS[:len(country_views)]),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Total Views: %{value:,.0f}<br>"
            "Share: %{percent}<br>"
            "<extra></extra>"
        ),
        textfont=dict(size=9),
        sort=False,
    ))

    fig.update_layout(
        autosize=False, height=H_BOT,
        title=dict(
            text=f"Views by Country — {short}",
            font=dict(size=9), x=0.5,
        ),
        annotations=[dict(
            text=f"<b>{short}</b>",
            x=0.5, y=0.5,
            font=dict(size=9, family="Segoe UI"),
            showarrow=False,
        )],
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="white",
        font=dict(family="Segoe UI"),
    )
    fig.update_traces(
        domain=dict(x=[0.05, 0.95], y=[0.05, 0.95]),
        textposition="outside",
        textinfo="label+percent",
        textfont=dict(size=8),
    )
    return fig


def fig_scatter(country=None):
    df = scatter_df.copy()
    if country:
        df = df[df["country_name"] == country]
    df = df.drop_duplicates(subset="video_id")
    viral = df[df["is_viral"]]
    if not viral.empty:
        sampled = []
        for cat in viral["category_name"].unique():
            sampled.append(
                viral[viral["category_name"]==cat].nlargest(3,"views")
            )
        df = pd.concat(sampled).drop_duplicates("video_id")
    else:
        df = df.nlargest(15, "views")
    if df.empty:
        return go.Figure(layout=dict(height=H_BOT,
                                     paper_bgcolor="white"))

    fig = go.Figure()

    # All videos are viral — circles coloured by category
    for cat in df["category_name"].unique():
        sub = df[df["category_name"] == cat]
        fig.add_trace(go.Scatter(
            x=sub["views"],
            y=sub["engagement_rate"],
            mode="markers",
            name=cat,
            marker=dict(
                symbol="circle",
                color=CATEGORY_COLORS.get(cat, "#AAAAAA"),
                size=10,
                opacity=0.85,
                line=dict(width=1.2,
                          color="rgba(255,255,255,0.7)"),
            ),
            customdata=sub[["channel_title","likes",
                            "days_to_trending"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Channel: %{customdata[0]}<br>"
                "Views: %{x:,.0f}<br>"
                "Engagement: %{y:.2f}%<br>"
                "Likes: %{customdata[1]:,.0f}<br>"
                "Days to trending: %{customdata[2]:.0f}<br>"
                " Viral — Top 1%<br>"
                "<extra></extra>"
            ),
            text=sub["title"],
            legendgroup=cat,
            showlegend=True,
        ))

    fig.update_layout(
        autosize=False, height=H_BOT,
        paper_bgcolor="white", plot_bgcolor="#f9f9f9",
        margin=dict(l=36, r=120, t=25, b=40),
        title=dict(
            text="Viral Videos (Top 1%) — Views vs Engagement",
            font=dict(size=9), x=0.5,
        ),
        legend=dict(
            title="",
            font=dict(size=7),
            itemsizing="constant",
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.01,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#ececec",
            borderwidth=1,
        ),
        font=dict(family="Segoe UI", size=9),
        xaxis=dict(
            title="Views",
            gridcolor="#ececec",
            zeroline=False,
            type="log",
            tickvals=[2e7,5e7,1e8,2e8,5e8,1e9],
            ticktext=["20M","50M","100M","200M","500M","1B"],
        ),
        yaxis=dict(
            title="Engagement (%)",
            gridcolor="#ececec",
            zeroline=False,
            ticksuffix="%",
        ),
    )
    return fig

def get_videos(country=None):
    df = clean_df.copy()
    if country:
        df = df[df["country_name"] == country]
    df = (df.sort_values("views", ascending=False)
            .drop_duplicates(subset="video_id", keep="first")
            .head(15))
    result = []
    for _, row in df.iterrows():
        result.append({
            "id":       str(row["video_id"]),
            "title":    str(row["title"]) if pd.notna(row["title"]) else "",
            "channel":  str(row["channel_title"]) if pd.notna(row["channel_title"]) else "",
            "category": str(row["category_name"]) if pd.notna(row["category_name"]) else "Unknown",
            "views":    int(row["views"]),
            "likes":    int(row["likes"]),
            "comments": int(row["comments"]),
            "tags":     row["tags"].split("|") if isinstance(row["tags"], str) else [],
        })
    return result


def fig_trending(videos, selected_id=None):
    if not videos:
        return go.Figure(layout=dict(height=H_BOT,
                                     paper_bgcolor="white"))
    vids   = list(reversed(videos))
    labels = [textwrap.shorten(v["title"], width=32, placeholder="…")
              for v in vids]
    opacs  = [0.2 if (selected_id and v["id"] != selected_id) else 1.0
              for v in vids]
    fig        = go.Figure()
    added_cats = set()
    for v, lbl, op in zip(vids, labels, opacs):
        color    = CATEGORY_COLORS.get(v["category"], "#AAAAAA")
        show_leg = v["category"] not in added_cats
        added_cats.add(v["category"])
        fig.add_trace(go.Bar(
            name=v["category"], y=[lbl], x=[v["views"]],
            orientation="h",
            marker_color=color, marker_opacity=op,
            marker_line=dict(width=0),
            customdata=[[v["id"]]],
            hovertemplate=(
                f"<b>{v['title']}</b><br>"
                f"Channel: {v['channel']}<br>"
                f"Views: %{{x:,.0f}}<extra></extra>"
            ),
            showlegend=show_leg, legendgroup=v["category"],
        ))
    fig.update_layout(
        barmode="overlay",
        autosize=False, height=H_BOT,
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0, r=6, t=28, b=4),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01,
            xanchor="left", x=0,
            font=dict(size=7, color="#444"),
            itemclick=False, itemsizing="constant",
        ),
        xaxis=dict(tickformat=".2s",
                   gridcolor="rgba(0,0,0,0.06)",
                   showline=False,
                   tickfont=dict(size=7, color="#555")),
        yaxis=dict(showgrid=False, showline=False,
                   tickfont=dict(size=7, color="#222"),
                   automargin=True),
        clickmode="event+select",
    )
    return fig


def make_detail(video):
    if not video:
        return html.Div()
    color = CATEGORY_COLORS.get(video["category"], "#888")
    return html.Div([
        html.Span(video["category"], style={
            "background": color, "color": "white",
            "borderRadius": "10px", "padding": "1px 8px",
            "fontSize": "9px", "fontWeight": "700",
            "marginRight": "4px",
        }),
        *[html.Span(f"#{t}", style={
            "background": "#EDEAE0", "borderRadius": "10px",
            "padding": "1px 6px", "fontSize": "9px",
            "marginRight": "3px", "color": "#333",
            "display": "inline-block",
        }) for t in video["tags"][:5]],
    ], style={"marginTop": "2px", "lineHeight": "2"})


# ══════════════════════════════════════════════════════════════
# PRE-BUILD INITIAL FIGURES
# ══════════════════════════════════════════════════════════════
_init_videos   = get_videos(DEFAULT)
_init_map      = fig_map()
_init_cats     = fig_categories(DEFAULT)
_init_heatmap  = fig_heatmap(DEFAULT, "avg_views")
_init_scatter  = fig_scatter(DEFAULT)
_init_trend    = fig_trending(_init_videos)

# ══════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════
app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "YouTube Trending 2026"

CARD = {
    "background":   "white",
    "borderRadius": "8px",
    "padding":      "8px 10px 4px 10px",
    "boxShadow":    "0 1px 6px rgba(0,0,0,0.09)",
    "overflow":     "hidden",
}
LBL = {
    "fontSize": "11px", "fontWeight": "700",
    "color": "#1a3a5c", "fontFamily": "Segoe UI,sans-serif",
    "marginBottom": "2px", "display": "block",
}
G = {"displayModeBar": False}

app.layout = html.Div(style={
    "fontFamily":      "Segoe UI, Arial, sans-serif",
    "backgroundColor": "#eef1f5",
    "width":           "100vw",
    "height":          "100vh",
    "display":         "grid",
    "gridTemplateRows": f"38px {H_TOP}px {H_BOT}px",
    "gap":             "6px",
    "padding":         "6px",
    "boxSizing":       "border-box",
    "overflow":        "hidden",
}, children=[

    # ── HEADER ────────────────────────────────────────────────
    html.Div(style={
        "background":"linear-gradient(90deg,#0f2744,#1a4a7a)",
        "borderRadius":"8px","display":"flex",
        "alignItems":"center","justifyContent":"space-between",
        "padding":"0 14px",
    }, children=[
        html.Div([
            html.Span(
                "YouTube Trending 2026  · The DNA of Viral Videos & Global Cultural Preferences",
                style={"color":"white","fontWeight":"bold","fontSize":"13px"}),
        ]),
        html.Div([
            html.Span(
                " Click a country to filter · Click a category to explore its channels",
                style={"color":"#90aac8","fontSize":"10px","fontStyle":"italic"}),
            html.Button("🔄 Reset", id="reset-btn", n_clicks=0, style={
                "marginLeft":"10px","fontSize":"9px",
                "padding":"2px 8px","borderRadius":"5px",
                "border":"1px solid #4a7ab5","background":"transparent",
                "color":"#90aac8","cursor":"pointer","display":"none",
            }),
        ]),
    ]),

    # ── ROW 1 : MAP (left)  +  TOP CATEGORIES (right) ────────
    html.Div(style={
        "display":"grid","gridTemplateColumns":"60% 40%","gap":"6px",
    }, children=[

        html.Div(style=CARD, children=[
            html.Span(" Global Overview",
                      style=LBL),
            dcc.Graph(id="world-map", figure=_init_map, config=G,
                      style={"height":f"{H_TOP}px"}),
        ]),

        html.Div(style=CARD, children=[
            html.Span(id="cat-title",
                      children=f"Top Categories — {DEFAULT}",
                      style=LBL),
            dcc.Graph(id="cat-chart", figure=_init_cats, config=G,
                      style={"height":f"{H_TOP}px"}),
        ]),
    ]),

    # ── ROW 2 : HEATMAP/CHANNELS · SCATTER · TRENDING ────────
    html.Div(style={
        "display":"grid",
        "gridTemplateColumns":"1fr 1fr 1fr",
        "gap":"6px",
    }, children=[

        # LEFT : heatmap OR channels
        html.Div(style=CARD, children=[
            html.Div(style={
                "display":"flex","justifyContent":"space-between",
                "alignItems":"center","marginBottom":"2px",
            }, children=[
                html.Span(id="left-title",
                          children=" Best Day & Hour ",
                          style=LBL),
                html.Div(id="metric-dd-wrapper", children=[
                    dcc.Dropdown(
                        id="metric-dd",
                        options=[
                            {"label":"Avg Views",      "value":"avg_views"},
                            {"label":"Avg Engagement", "value":"avg_engagement"},
                            {"label":"Total Videos",   "value":"total_videos"},
                        ],
                        value="avg_views", clearable=False,
                        style={"fontSize":"9px","width":"120px"},
                    ),
                ]),
                html.Button("← Back", id="back-btn", n_clicks=0, style={
                    "fontSize":"9px","padding":"2px 8px",
                    "borderRadius":"5px","cursor":"pointer",
                    "border":"1px solid #4a7ab5",
                    "background":"#EBF3FB","color":"#1a3a5c",
                    "display":"none",
                }),
            ]),
            dcc.Graph(id="left-chart", figure=_init_heatmap, config=G,
                      style={"height":f"{H_BOT}px"}),
            dcc.Store(id="selected-cat", data=None),
        ]),

        # MIDDLE : scatterplot
        html.Div(style=CARD, children=[
            html.Span(id="scatter-title",
                      children=" Views vs Engagement — Viral Videos",
                      style=LBL),
            dcc.Graph(id="scatter", figure=_init_scatter, config=G,
                      style={"height":f"{H_BOT}px"}),
        ]),

        # RIGHT : trending videos
        html.Div(style=CARD, children=[
            html.Span(id="trend-title",
                      children=f" Top 15 Trending Videos — {DEFAULT}",
                      style=LBL),
            dcc.Graph(id="trend-bar", figure=_init_trend, config=G,
                      style={"height":f"{H_BOT}px"}),
            html.Div(id="trend-detail"),
            dcc.Store(id="sel-vid", data=None),
        ]),
    ]),

])


# ══════════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════════

# 1. World Map
@app.callback(
    Output("world-map","figure"),
    Output("reset-btn","style"),
    Input("world-map","clickData"),
    Input("reset-btn","n_clicks"),
)
def cb_map(click_data, _):
    if ctx.triggered_id == "reset-btn":
        click_data = None
    sel = get_country(click_data)
    btn = {
        "marginLeft":"10px","fontSize":"9px",
        "padding":"2px 8px","borderRadius":"5px",
        "border":"1px solid #4a7ab5","background":"transparent",
        "color":"#90aac8","cursor":"pointer",
        "display":"block" if sel else "none",
    }
    return fig_map(sel), btn


# 2. Top Categories
@app.callback(
    Output("cat-chart","figure"),
    Output("cat-title","children"),
    Input("world-map","clickData"),
    Input("reset-btn","n_clicks"),
)
def cb_cats(click_data, _):
    if ctx.triggered_id == "reset-btn":
        click_data = None
    country = get_country(click_data) or DEFAULT
    return fig_categories(country), f"Top Categories — {country}"


# 3. Left panel : heatmap ↔ channels
@app.callback(
    Output("left-chart",        "figure"),
    Output("left-title",        "children"),
    Output("metric-dd-wrapper", "style"),
    Output("back-btn",          "style"),
    Output("selected-cat",      "data"),
    Input("cat-chart",          "clickData"),
    Input("back-btn",           "n_clicks"),
    Input("world-map",          "clickData"),
    Input("reset-btn",          "n_clicks"),
    Input("metric-dd",          "value"),
    State("selected-cat",       "data"),
)
def cb_left(cat_click, back_clicks, map_click, reset_clicks,
            metric, selected_cat):
    triggered = ctx.triggered_id

    BACK_BTN_HIDDEN = {
        "fontSize":"9px","padding":"2px 8px","borderRadius":"5px",
        "cursor":"pointer","border":"1px solid #4a7ab5",
        "background":"#EBF3FB","color":"#1a3a5c","display":"none",
    }
    BACK_BTN_SHOWN = {**BACK_BTN_HIDDEN, "display":"block"}

    if triggered in ("back-btn","world-map","reset-btn"):
        if triggered == "reset-btn":
            map_click = None
        country = get_country(map_click) or DEFAULT
        return (fig_heatmap(country, metric),
                " Best Day & Hour to publish",
                {"display":"block"}, BACK_BTN_HIDDEN, None)

    if triggered == "cat-chart" and cat_click:
        try:
            category = cat_click["points"][0]["y"]
        except Exception:
            category = None
        if category:
            return (fig_channels_for_category(category),
                    f" Top Channels — {category}",
                    {"display":"none"}, BACK_BTN_SHOWN, category)

    if triggered == "metric-dd" and not selected_cat:
        country = get_country(map_click) or DEFAULT
        return (fig_heatmap(country, metric),
                " Best Day & Hour — Task 1",
                {"display":"block"}, BACK_BTN_HIDDEN, None)

    country = get_country(map_click) or DEFAULT
    return (fig_heatmap(country, metric),
            " Best Day & Hour — Task 1",
            {"display":"block"}, BACK_BTN_HIDDEN, None)


# 4. Middle panel : scatterplot ↔ donut
@app.callback(
    Output("scatter",       "figure"),
    Output("scatter-title", "children"),
    Input("world-map",      "clickData"),
    Input("reset-btn",      "n_clicks"),
    Input("left-chart",     "clickData"),
    State("selected-cat",   "data"),
)
def cb_scatter(map_click, _, left_click, selected_cat):
    triggered = ctx.triggered_id

    # Channel clicked → show donut
    if triggered == "left-chart" and left_click and selected_cat:
        try:
            channel = left_click["points"][0]["y"]
        except Exception:
            channel = None
        if channel:
            return (
                fig_donut(channel),
                f" Views by Country — {channel[:25]}",
            )

    # Otherwise show scatterplot
    if triggered == "reset-btn":
        map_click = None
    return (
        fig_scatter(get_country(map_click)),
        " Views vs Engagement — Viral Videos",
    )


# 5. Trending Videos
@app.callback(
    Output("trend-bar",    "figure"),
    Output("trend-detail", "children"),
    Output("trend-title",  "children"),
    Output("sel-vid",      "data"),
    Input("world-map",     "clickData"),
    Input("reset-btn",     "n_clicks"),
    Input("trend-bar",     "clickData"),
    State("sel-vid",       "data"),
)
def cb_trending(map_click, _, bar_click, cur_vid):
    triggered = ctx.triggered_id
    if triggered == "reset-btn":
        map_click = None
    country = get_country(map_click)
    videos  = get_videos(country)
    title   = f" Top 15 Trending — {country or 'Global'}"
    if triggered == "trend-bar" and bar_click:
        try:
            vid_id = bar_click["points"][0]["customdata"][0]
        except Exception:
            vid_id = None
        new_id = None if vid_id == cur_vid else vid_id
        video  = next((v for v in videos if v["id"] == new_id), None)
        return (fig_trending(videos, new_id),
                make_detail(video), title, new_id)
    return fig_trending(videos), make_detail(None), title, None


# ══════════════════════════════════════════════════════════════
server = app.server

if __name__ == "__main__":
    app.run(debug=False)
