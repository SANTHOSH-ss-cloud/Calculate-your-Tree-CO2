import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import os

# Load dataset
df = pd.read_csv("species_data.csv")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

st.title("🌳 Tree CO₂ Sequestration Estimator")

# UI Inputs
species = st.selectbox("Choose a Tree Species", df["common_name"])
years = st.slider("Select Time Period (years)", 1, 50, 20)
num_trees = st.number_input("Enter Number of Trees", min_value=1, value=100)

# Data for selected tree
tree_data = df[df["common_name"] == species].iloc[0]
growth_rate = tree_data["avg_dbh_growth"]
carbon_fraction = tree_data["carbon_fraction"]
survival_rate = tree_data["survival_rate"]

# CO2 estimation model
def calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees=1):
    avg_dbh = growth_rate * years
    biomass_kg = 0.25 * (avg_dbh ** 2) * years
    carbon_kg = biomass_kg * carbon_fraction
    co2_kg = carbon_kg * 3.67
    total_kg = co2_kg * num_trees * survival_rate
    return total_kg / 1000  # metric tons

total_co2_tons = calculate_co2(growth_rate, carbon_fraction, survival_rate, years, num_trees)

st.success(f"🌱 Estimated CO₂ Sequestration: {total_co2_tons:.2f} metric tons over {years} years.")

# Generate graph
def create_graph():
    x_vals = list(range(1, 1001, 50))
    y_vals = [calculate_co2(growth_rate, carbon_fraction, survival_rate, years, n) for n in x_vals]

    fig, ax = plt.subplots()
    ax.plot(x_vals, y_vals, marker='o', color='green')
    ax.set_title(f"CO₂ Sequestered vs Number of Trees\n({species} over {years} years)")
    ax.set_xlabel("Number of Trees")
    ax.set_ylabel("CO₂ Sequestered (metric tons)")
    ax.grid(True)

    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='PNG')
    img_buffer.seek(0)
    plt.close(fig)
    return img_buffer

# Graph display in Streamlit
st.subheader(f"📈 CO₂ Sequestered vs Number of Trees for {species}")
graph_image = create_graph()
st.image(graph_image, caption=f"CO₂ Sequestration for {species}", use_column_width=True)

# PDF generator with graph
def generate_pdf_with_graph(graph_image):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Tree CO2 Sequestration Report", ln=True, align='C')
    
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(190, 10, f"Species: {species}", ln=True)
    pdf.cell(190, 10, f"Years: {years}", ln=True)
    pdf.cell(190, 10, f"Number of Trees: {num_trees}", ln=True)
    pdf.cell(190, 10, f"Estimated CO2 Sequestered: {total_co2_tons:.2f} metric tons", ln=True)
    pdf.ln(5)
    pdf.cell(190, 10, f"Model Parameters:", ln=True)
    pdf.cell(190, 10, f"- Avg. DBH Growth: {growth_rate} cm/year", ln=True)
    pdf.cell(190, 10, f"- Carbon Fraction: {carbon_fraction}", ln=True)
    pdf.cell(190, 10, f"- Survival Rate: {survival_rate}", ln=True)

    # Save the graph temporarily and insert into PDF
    image_path = "/tmp/temp_graph.png"
    with open(image_path, "wb") as f:
        f.write(graph_image.getbuffer())
    pdf.ln(10)
    pdf.image(image_path, x=10, w=180)
    os.remove(image_path)  # Clean up

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# PDF download button
pdf_data = generate_pdf_with_graph(graph_image)
st.download_button(
    label="📄 Download Report with Graph (PDF)",
    data=pdf_data,
    file_name=f"{species.replace(' ', '_')}_CO2_Report.pdf",
    mime="application/pdf"
)
