<script>
  fetch("http://127.0.0.1:8889/ipc", { 
    method: "POST",
    headers: {
      "Content-Type": "text/plain"
    }
  })
  .then(res => res.text())
  .then(data => {
    console.log("Received from service:", data);
    // you can assign it to a JS variable
    var ipcValue = data;
  })
  .catch(err => console.error("IPC send error:", err));
</script>
