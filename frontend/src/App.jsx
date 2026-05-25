import { useState } from 'react'
import './App.css'

export default function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setResult(null)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('http://localhost:8000/identify', {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (data.error) setError(data.error)
      else setResult(data)
    } catch {
      setError('Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>Soundprint</h1>
      <p className="tagline">Upload a song to identify its genre</p>

      <form onSubmit={handleSubmit}>
        <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files[0])} />
        <button type="submit" disabled={!file || loading}>
          {loading ? 'Identifying...' : 'Identify'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result">
          <h2>{result.title}</h2>
          <p className="artist">{result.artist}</p>
          <p className="album">{result.album} · {result.release_date?.slice(0, 4)}</p>

          <div className="genres">
            {result.genres?.[0] && <span className="genre">{result.genres[0]}</span>}
            {result.subgenre && <span className="genre subgenre">{result.subgenre}</span>}
          </div>

          <a href={result.spotify_url} target="_blank" rel="noreferrer" className="spotify-link">
            Open on Spotify
          </a>

          {result.similar_songs?.length > 0 && (
            <div className="similar">
              <h3>Similar Songs</h3>
              <ul>
                {result.similar_songs.map((s, i) => (
                  <li key={i}>
                    <a href={s.spotify_url} target="_blank" rel="noreferrer">
                      {s.title} — {s.artist}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
