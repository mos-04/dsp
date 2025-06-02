import streamlit as st
import socket
import json
import threading
import time

# Helper function to send command to backend node (running locally or remotely)
def send_command(command, host='localhost', port=5000):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(command.encode())

        # For some commands, expect a response (e.g., history, chain)
        response = s.recv(8192).decode()
        s.close()
        return response
    except Exception as e:
        return f"Error: {e}"

# Streamlit UI starts here
st.title("Distributed Supply Chain Tracker")

host = st.text_input("Node Host", value="localhost")
port = st.number_input("Node Port", value=5000, step=1)

st.sidebar.header("Peer Connection")
peer_ip = st.sidebar.text_input("Peer IP")
peer_port = st.sidebar.number_input("Peer Port", min_value=1, max_value=65535, step=1)
if st.sidebar.button("Connect to Peer"):
    cmd = f"connect {peer_ip} {peer_port}"
    result = send_command(cmd, host, port)
    st.sidebar.success(f"Sent: {cmd}")

st.header("Add Supply Chain Event")
with st.form("mine_form"):
    product_id = st.text_input("Product ID")
    status = st.text_input("Status (e.g., Shipped, Delivered)")
    location = st.text_input("Location")
    submitted = st.form_submit_button("Mine and Broadcast")
    if submitted:
        if product_id and status and location:
            cmd = f"mine {product_id} {status} {location}"
            result = send_command(cmd, host, port)
            st.success("Event mined and broadcasted!")
        else:
            st.error("Please fill all fields.")

st.header("View Product History")
product_query = st.text_input("Enter Product ID to query history")
if st.button("Get History"):
    if product_query:
        cmd = f"history {product_query}"
        result = send_command(cmd, host, port)
        st.text_area("History:", value=result, height=200)
    else:
        st.error("Enter a valid product ID")

st.header("Blockchain Summary")
if st.button("Show Chain"):
    cmd = "chain"
    result = send_command(cmd, host, port)
    st.text_area("Blockchain:", value=result, height=300)

st.header("Peers")
if st.button("Show Peers"):
    cmd = "peers"
    result = send_command(cmd, host, port)
    st.write(result)
