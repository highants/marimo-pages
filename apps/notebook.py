import marimo

__generated_with = "0.17.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go

    # UI elements for paper airplane parameters
    mass_kg = mo.ui.slider(
        start=0.001,
        stop=0.05,
        step=0.001,
        value=0.005,
        label="質量 (kg)",
        full_width=True,
    )
    initial_velocity_mps = mo.ui.slider(
        start=1,
        stop=30,
        step=1,
        value=10,
        label="初速 (m/s)",
        full_width=True,
    )
    launch_angle_deg = mo.ui.slider(
        start=0,
        stop=90,
        step=1,
        value=30,
        label="発射角度 (度)",
        full_width=True,
    )
    drag_coefficient = mo.ui.slider(
        start=0.01,
        stop=1.0,
        step=0.01,
        value=0.1,
        label="抗力係数",
        full_width=True,
    )
    wing_area_sqm = mo.ui.slider(
        start=0.001,
        stop=0.1,
        step=0.001,
        value=0.01,
        label="翼面積 (m²)",
        full_width=True,
    )

    mo.hstack([
        mo.vstack([mass_kg, initial_velocity_mps]),
        mo.vstack([launch_angle_deg, drag_coefficient]),
        mo.vstack([wing_area_sqm])
    ])
    return (
        drag_coefficient,
        go,
        initial_velocity_mps,
        launch_angle_deg,
        mass_kg,
        mo,
        np,
        pd,
        wing_area_sqm,
    )


@app.cell
def _(
    drag_coefficient,
    initial_velocity_mps,
    launch_angle_deg,
    mass_kg,
    np,
    pd,
    wing_area_sqm,
):
    # Constants
    GRAVITY = 9.81  # m/s^2
    AIR_DENSITY = 1.225  # kg/m^3 (standard air density at sea level)

    def simulate_trajectory(
        mass: float,
        initial_velocity: float,
        launch_angle: float,
        drag_coefficient: float,
        wing_area: float,
        time_step: float = 0.01,
        max_time: float = 100.0
    ) -> pd.DataFrame:
        """
        Simulates the trajectory of a paper airplane with air resistance.
        """
        angle_rad = np.deg2rad(launch_angle)

        # Initial conditions
        x, y = 0.0, 0.0
        vx = initial_velocity * np.cos(angle_rad)
        vy = initial_velocity * np.sin(angle_rad)

        time_points = [0.0]
        x_points = [x]
        y_points = [y]

        t = 0.0
        while y >= 0 and t < max_time:
            # Calculate drag force magnitude
            speed = np.sqrt(vx**2 + vy**2)
            drag_force_magnitude = 0.5 * AIR_DENSITY * speed**2 * drag_coefficient * wing_area

            if speed > 0:
                # Drag force components (opposite to velocity)
                drag_fx = -drag_force_magnitude * (vx / speed)
                drag_fy = -drag_force_magnitude * (vy / speed)
            else:
                drag_fx, drag_fy = 0, 0

            # Net forces
            net_fx = drag_fx
            net_fy = drag_fy - mass * GRAVITY

            # Accelerations
            ax = net_fx / mass
            ay = net_fy / mass

            # Update velocities
            vx += ax * time_step
            vy += ay * time_step

            # Update positions
            x += vx * time_step
            y += vy * time_step
            t += time_step

            time_points.append(t)
            x_points.append(x)
            y_points.append(y)

        return pd.DataFrame({
            "time": time_points,
            "x_position": x_points,
            "y_position": y_points
        })

    trajectory_df = simulate_trajectory(
        mass=mass_kg.value,
        initial_velocity=initial_velocity_mps.value,
        launch_angle=launch_angle_deg.value,
        drag_coefficient=drag_coefficient.value,
        wing_area=wing_area_sqm.value
    )
    return (trajectory_df,)


@app.cell
def _(go, trajectory_df):
    # Create the plot
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trajectory_df["x_position"],
        y=trajectory_df["y_position"],
        mode='lines',
        name='軌道',
        line=dict(color='blue', width=2)
    ))

    fig.update_layout(
        title='紙飛行機の軌道シミュレーション',
        xaxis_title='水平距離 (m)',
        yaxis_title='高さ (m)',
        yaxis_range=[0, max(trajectory_df["y_position"]) * 1.1], # Ensure y-axis starts at 0 and has some padding
        xaxis_range=[0, max(trajectory_df["x_position"]) * 1.1], # Ensure x-axis starts at 0 and has some padding
        hovermode="x unified",
        template="plotly_white"
    )

    fig.update_yaxes(scaleanchor="x", scaleratio=1) # Keep aspect ratio for better visualization

    fig
    return


@app.cell
def _(mo, trajectory_df):
    mo.md(f"""
    ### シミュレーション結果

    紙飛行機は水平距離 **{trajectory_df["x_position"].iloc[-1]:.2f} m** を飛行し、
    最高到達高度は **{trajectory_df["y_position"].max():.2f} m** でした。
    """)
    return


if __name__ == "__main__":
    app.run()
