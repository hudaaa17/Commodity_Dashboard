import plotly.graph_objects as go


def plot_trend(df, commodity):
    """
    Professional interactive trend chart

    Input:
        df → DataFrame with Date, price
        commodity → string

    Returns:
        Plotly figure
    """

    if df.empty:
         print(f"⚠️ No data to plot for {commodity}")

    df = df.copy()

    # ----------------------------
    # Add day index (1 → 30)
    # ----------------------------
    df["day"] = range(1, len(df) + 1)

    # ----------------------------
    # Create figure
    # ----------------------------
    fig = go.Figure()

    # Main trend line
    fig.add_trace(
        go.Scatter(
            x=df["day"],
            y=df["price"],
            mode="lines+markers",
            name=commodity,
            line=dict(width=3),
            marker=dict(size=5),
            hovertemplate="Day %{x}<br>Price: %{y:.2f}<extra></extra>"
        )
    )

    # ----------------------------
    # Highlight FINAL DAY (Day 30)
    # ----------------------------
    final_day = df.iloc[-1]

    fig.add_trace(
        go.Scatter(
            x=[final_day["day"]],
            y=[final_day["price"]],
            mode="markers+text",
            marker=dict(size=10),
            text=[f"{final_day['price']:.2f}"],
            textposition="top center",
            name="Final (Day 30)",
            hoverinfo="skip"
        )
    )

    # ----------------------------
    # Week markers (vertical lines)
    # ----------------------------
    week_marks = [7, 14, 21, 30]

    for w in week_marks:
        fig.add_vline(
            x=w,
            line_width=1,
            line_dash="dot"
        )

    # ----------------------------
    # Layout (professional look)
    # ----------------------------
    fig.update_layout(
        title=f"{commodity} Price Forecast (30 Days)",
        xaxis_title="Forecast Horizon (Days)",
        yaxis_title="Price",

        template="plotly_white",

        hovermode="x unified",

        xaxis=dict(
            tickmode="array",
            tickvals=[1, 7, 14, 21, 30],
            ticktext=["Day 1", "Week 1", "Week 2", "Week 3", "Day 30"]
        ),

        margin=dict(l=40, r=20, t=50, b=40),

        height=400
    )

    return fig