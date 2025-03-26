import streamlit as st

st.title("Streamlit Tooltip Demo 🎯")

# Basic tooltip example
st.markdown("### Basic Tooltip")
st.markdown("Hover over this text to see a tooltip", help="This is a basic tooltip!")

# Tooltip with markdown formatting
st.markdown("### Tooltip with Markdown")
st.markdown("Hover here for formatted tooltip", help="**Bold text** and *italic text* in tooltip!")

# Tooltip with emoji
st.markdown("### Tooltip with Emoji")
st.markdown("Hover for emoji tooltip", help="Here's a tooltip with emojis: 🎉 🎨 🚀")

# Tooltip with colored text
st.markdown("### Tooltip with Colored Text")
st.markdown("Hover for colored tooltip", help=":red[Red text] and :blue[blue text] in tooltip!")

# Tooltip with LaTeX
st.markdown("### Tooltip with LaTeX")
st.markdown("Hover for LaTeX tooltip", help="$E = mc^2$")

# Tooltip with multiple lines
st.markdown("### Multi-line Tooltip")
st.markdown("Hover for multi-line tooltip", help="""This is a multi-line tooltip.
- First line
- Second line
- Third line""")

# Tooltip with code
st.markdown("### Tooltip with Code")
st.markdown("Hover for code tooltip", help="```python\nprint('Hello, World!')\n```")

# Tooltip with link
st.markdown("### Tooltip with Link")
st.markdown("Hover for link tooltip", help="[Click here](https://streamlit.io)")

# Tooltip with table
st.markdown("### Tooltip with Table")
st.markdown("Hover for table tooltip", help="""| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |""") 