<template>
  <div class="upload-wrapper">
    <div class="upload-container">
      <div class="upload-header">
        <h1>Upload Documents</h1>
        <p>Upload PDFs or plain text files to add them to the RAG vector store.</p>
        <router-link class="back-link" to="/">← Back to chat</router-link>
      </div>

      <div class="upload-body">
        <label class="file-label" for="file-input">Choose a file</label>
        <input 
          id="file-input" 
          ref="fileInputRef"
          type="file" 
          accept=".pdf,.txt" 
          :disabled="loading"
        />

        <button 
          id="upload-btn" 
          class="upload-btn" 
          @click="uploadFile"
          :disabled="loading"
        >
          {{ loading ? 'Uploading...' : 'Upload & Index' }}
        </button>

        <div 
          id="status" 
          class="upload-status" 
          :class="{ error: isError }"
          aria-live="polite"
        >
          {{ statusMessage }}
        </div>
      </div>

      <div class="upload-notes">
        <p><strong>Note:</strong> Uploaded documents are indexed locally and used by the RAG pipeline for knowledge retrieval.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const fileInputRef = ref(null)
const statusMessage = ref('')
const isError = ref(false)
const loading = ref(false)

async function uploadFile() {
  statusMessage.value = ''
  isError.value = false

  const files = fileInputRef.value?.files
  if (!files || files.length === 0) {
    statusMessage.value = 'Please select a file to upload.'
    isError.value = true
    return
  }

  const file = files[0]
  const formData = new FormData()
  formData.append('file', file)

  loading.value = true

  try {
    const response = await fetch('/upload-dox', {
      method: 'POST',
      body: formData,
    })

    const result = await response.json()
    console.log('Upload response:', result)

    if (!response.ok) {
      throw new Error(result.detail || result.error || 'Upload failed')
    }

    statusMessage.value = `Upload complete! Indexed ${result.chunks_added} chunks from ${result.file}.`
    isError.value = false
    
    // Clear input
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  } catch (error) {
    statusMessage.value = `Error: ${error.message}`
    isError.value = true
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.upload-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 28px 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'DM Sans', sans-serif;
  color: #333;
}

.upload-container {
  width: 100%;
  max-width: 620px;
  background-color: #ffffff;
  border-radius: 16px;
  padding: 26px 28px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  gap: 14px;
  text-align: left;
}

.upload-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #111;
}

.upload-header p {
  margin: 0 0 14px 0;
  font-size: 13px;
  color: #4a4a4a;
}

.back-link {
  display: inline-block;
  margin-top: 10px;
  font-size: 13px;
  color: #667eea;
  text-decoration: none;
}

.back-link:hover {
  text-decoration: underline;
}

.upload-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-label {
  font-weight: 600;
  font-size: 13px;
  color: #555;
}

#file-input {
  border-radius: 10px;
  padding: 10px;
  border: 2px solid #e0e0e0;
  background: #fdfdfd;
}

.upload-btn {
  padding: 12px 18px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.25s ease;
  font-family: inherit;
}

.upload-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(102, 126, 234, 0.25);
}

.upload-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.upload-status {
  font-size: 13px;
  color: #333;
  min-height: 24px;
  word-break: break-all;
}

.upload-status.error {
  color: #b22828;
}

.upload-notes {
  font-size: 12px;
  color: #555;
  padding-top: 10px;
  border-top: 1px solid #e8e8e8;
}
</style>
