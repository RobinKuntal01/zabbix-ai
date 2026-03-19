document.addEventListener("DOMContentLoaded", () => {
    const uploadBtn = document.getElementById("upload-btn");
    const fileInput = document.getElementById("file-input");

    uploadBtn.addEventListener("click", async () => {
        const statusEl = document.getElementById("status");
        statusEl.textContent = "";

        if (!fileInput.files || fileInput.files.length === 0) {
            statusEl.textContent = "Please select a file to upload.";
            statusEl.classList.add("error");
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("file", file);

        uploadBtn.disabled = true;
        uploadBtn.textContent = "Uploading...";
        statusEl.classList.remove("error");

        try {
            const response = await fetch("/upload-dox", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();
            console.log("Upload response:", result);
            if (!response.ok) {
                throw new Error(result.detail || result.error || "Upload failed");
            }

            statusEl.textContent = `Upload complete! Indexed ${result.chunks_added} chunks from ${result.file}.`;
            statusEl.classList.remove("error");
            fileInput.value = "";
        } catch (error) {
            statusEl.textContent = `Error: ${error.message}`;
            statusEl.classList.add("error");
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = "Upload & Index";
        }
    });
});
