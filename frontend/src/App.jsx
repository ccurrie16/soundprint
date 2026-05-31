import { useState } from 'react'
import './App.css'

function Result({ result }) {
  const gi = result.genre_info || {}

  return (
    <div className="result">
      <div className="result-top">
        {result.album_art && (
          <img src={result.album_art} alt="Album art" className="album-art" />
        )}
        <div className="result-info">
          <h2>{result.title}</h2>
          <p className="artist">{result.artist}</p>
          <p className="album">{result.album} · {result.release_date?.slice(0, 4)}</p>
          <div className="genres">
            {result.genres?.map((g, i) => (
              <span key={i} className="genre">{g}</span>
            ))}
          </div>
          <a href={result.spotify_url} target="_blank" rel="noreferrer" className="spotify-link">
            Open on Spotify ↗
          </a>
        </div>
      </div>

      {gi.primary_genre && (
        <div className="genre-breakdown">
          <div className="breakdown-grid">
            {gi.primary_genre && <div className="breakdown-item"><span className="breakdown-label">Genre</span><span className="breakdown-value">{gi.primary_genre}</span></div>}
            {gi.subgenre && <div className="breakdown-item"><span className="breakdown-label">Subgenre</span><span className="breakdown-value">{gi.subgenre}</span></div>}
            {gi.mood && <div className="breakdown-item"><span className="breakdown-label">Mood</span><span className="breakdown-value">{gi.mood}</span></div>}
            {gi.era && <div className="breakdown-item"><span className="breakdown-label">Era</span><span className="breakdown-value">{gi.era}</span></div>}
          </div>
          {gi.description && <p className="genre-description">{gi.description}</p>}
        </div>
      )}

      {result.similar_songs?.length > 0 && (
        <div className="similar">
          <h3>Similar Songs</h3>
          <ul>
            {result.similar_songs.map((s, i) => (
              <li key={i}>
                <a href={s.spotify_url} target="_blank" rel="noreferrer">
                  <span className="similar-title">{s.title}</span>
                  <span className="similar-artist">{s.artist}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}


function UploadTab() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setResult(null)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('https://soundprint-production.up.railway.app/identify', {
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

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped && dropped.type.startsWith('audio/')) setFile(dropped)
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        <label
          className={`file-drop ${file ? 'has-file' : ''} ${dragging ? 'dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files[0])} />
          {file ? <span>{file.name}</span> : <span>{dragging ? 'Drop it!' : 'Choose or drag an audio file'}</span>}
        </label>
        <button type="submit" disabled={!file || loading}>
          {loading ? <span className="spinner" /> : 'Identify'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && <Result result={result} />}
    </>
  )
}

function SearchTab() {
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingId, setLoadingId] = useState(null)
  const [error, setError] = useState(null)

  async function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setSearchResults([])
    setResult(null)
    setError(null)

    try {
      const res = await fetch(`https://soundprint-production.up.railway.app/search?q=${encodeURIComponent(query)}`)
      const data = await res.json()
      setSearchResults(data)
    } catch {
      setError('Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }

  async function handleSelect(track_id) {
    setLoadingId(track_id)
    setResult(null)
    setError(null)

    try {
      const res = await fetch(`https://soundprint-production.up.railway.app/track/${track_id}`)
      const data = await res.json()
      if (data.error) setError(data.error)
      else {
        setResult(data)
        setSearchResults([])
      }
    } catch {
      setError('Failed to connect to server')
    } finally {
      setLoadingId(null)
    }
  }

  return (
    <>
      <form onSubmit={handleSearch}>
        <input
          className="search-input"
          type="text"
          placeholder="Search for a song or artist..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={!query.trim() || loading}>
          {loading ? <span className="spinner" /> : 'Search'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {searchResults.length > 0 && (
        <ul className="search-results">
          {searchResults.map((t) => (
            <li key={t.track_id}>
              <button className="search-result-btn" onClick={() => handleSelect(t.track_id)} disabled={loadingId === t.track_id}>
                {t.album_art && <img src={t.album_art} alt="" className="search-thumb" />}
                <div className="search-result-info">
                  <span className="similar-title">{t.title}</span>
                  <span className="similar-artist">{t.artist} · {t.album}</span>
                </div>
                {loadingId === t.track_id && <span className="spinner dark" />}
              </button>
            </li>
          ))}
        </ul>
      )}

      {result && <Result result={result} />}
    </>
  )
}

export default function App() {
  const [tab, setTab] = useState('upload')

  return (
    <div className="app">
      <header>
        <h1>Soundprint</h1>
        <p className="tagline">Identify any song's genre</p>
      </header>

      <div className="tabs">
        <button className={`tab ${tab === 'upload' ? 'active' : ''}`} onClick={() => setTab('upload')}>
          Upload
        </button>
        <button className={`tab ${tab === 'search' ? 'active' : ''}`} onClick={() => setTab('search')}>
          Search
        </button>
      </div>

      {tab === 'upload' ? <UploadTab /> : <SearchTab />}
    </div>
  )
}
