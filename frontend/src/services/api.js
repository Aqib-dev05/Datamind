import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const api = axios.create({ baseURL: BASE })

export const uploadFile = async (file) => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/upload', form)
  return data
}

export const fetchQuestions = async (fileId) => {
  const { data } = await api.get(`/questions/${fileId}`)
  return data
}

export const processFile = async (fileId, answers, outputFormat) => {
  const { data } = await api.post('/process', {
    file_id: fileId,
    answers,
    output_format: outputFormat,
  })
  return data
}

export const getDownloadUrl = (fileId, fmt) =>
  `${BASE}/download/${fileId}/${fmt}`
