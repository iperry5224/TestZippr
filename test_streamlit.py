import streamlit as st

st.set_page_config(page_title="Test App", page_icon="✅")

st.title("✅ Streamlit is Working!")
st.write("If you can see this, Streamlit is running correctly.")

st.markdown("---")
st.header("Quick Test")
if st.button("Click Me"):
    st.success("Button works!")
    st.balloons()

