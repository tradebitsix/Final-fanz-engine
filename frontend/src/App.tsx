import { useEffect, useMemo, useState } from 'react'
import { convert, createExportToken, downloadUrl, getArtifact, health } from './api'

export default function App() {
  const [apiOk, setApiOk] = useState(false)
  const [apiBrand, setApiBrand] = useState("")
  const [error, setError] = useState("")
  const [mode, setMode] = useState("plan")
  const [raw, setRaw] = useState("")
  const [artifactId, setArtifactId] = useState("")
  const [artifact, setArtifact] = useState<any>(null)
  const [busy, setBusy] = useState(false)

  const canConvert = useMemo(()=> raw.trim().length>0 && !busy, [raw,busy])

  useEffect(()=>{
    (async()=>{
      try{
        const h = await health()
        setApiOk(h?.status==="ok")
        setApiBrand(h?.brand || "")
      }catch(e:any){
        setError(e?.message || String(e))
      }
    })()
  },[])

  async function doConvert(){
    setError(""); setBusy(true)
    try{
      const resp = await convert(raw, mode)
      const id = resp?.id
      setArtifactId(id)
      const art = await getArtifact(id)
      setArtifact(art)
    }catch(e:any){ setError(e?.message || String(e)) }
    finally{ setBusy(false) }
  }

  async function loadArtifact(){
    setError(""); setBusy(true)
    try{
      const art = await getArtifact(artifactId.trim())
      setArtifact(art)
    }catch(e:any){ setError(e?.message || String(e)) }
    finally{ setBusy(false) }
  }

  async function downloadZip(){
    setError(""); setBusy(true)
    try{
      const t = await createExportToken(artifact.id)
      const url = downloadUrl(t.token)
      window.location.href = url
    }catch(e:any){ setError(e?.message || String(e)) }
    finally{ setBusy(false) }
  }

  return (
    <div className="container">
      <div className="card">
        <div style={{display:'flex', justifyContent:'space-between', gap:12, flexWrap:'wrap', alignItems:'baseline'}}>
          <div>
            <div style={{fontSize:22, fontWeight:800}}>Fans of the One</div>
            <div className="small">Piece 4 — Production Glue (token download + migrations + deploy configs)</div>
          </div>
          <div className="small mono">API: {apiOk ? `OK ${apiBrand?`(${apiBrand})`:''}` : 'NOT CONNECTED'}</div>
        </div>
        <hr/>
        <div className="row">
          <div style={{flex:'1 1 180px'}}>
            <div className="small">Mode</div>
            <select className="select" value={mode} onChange={(e)=>setMode(e.target.value)}>
              <option value="plan">Plan</option>
              <option value="product">Product</option>
              <option value="code">Code</option>
              <option value="decision">Decision</option>
            </select>
          </div>
          <div style={{flex:'2 1 280px'}}>
            <div className="small">Artifact ID (load existing)</div>
            <div className="row" style={{gap:8}}>
              <input className="input" value={artifactId} onChange={(e)=>setArtifactId(e.target.value)} placeholder="paste artifact id..." />
              <button className="button" onClick={loadArtifact} disabled={!artifactId.trim() || busy}>Load</button>
            </div>
          </div>
        </div>
        <div style={{marginTop:12}}>
          <div className="small">Raw input</div>
          <textarea className="textarea" rows={9} value={raw} onChange={(e)=>setRaw(e.target.value)} placeholder="paste your raw input here..." />
        </div>
        <div style={{display:'flex', gap:10, marginTop:12, flexWrap:'wrap'}}>
          <button className="button" onClick={doConvert} disabled={!canConvert}>{busy ? "Working..." : "Convert → Artifact"}</button>
          {artifact?.id && <button className="button" onClick={downloadZip} disabled={busy}>Download Artifact ZIP</button>}
        </div>
        {error && <div style={{marginTop:12, color:'#ff8a8a'}} className="mono">{error}</div>}
      </div>

      {artifact && (
        <div className="card" style={{marginTop:16}}>
          <div style={{display:'flex', justifyContent:'space-between', gap:12, flexWrap:'wrap'}}>
            <div>
              <div style={{fontSize:16, fontWeight:800}}>Artifact</div>
              <div className="small mono">{artifact.id}</div>
            </div>
            <div className="small">{artifact.created_at ? `Created: ${artifact.created_at}` : ""}</div>
          </div>
          <hr/>
          <div className="small">Structured output</div>
          <pre className="mono" style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(artifact.structured_output, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
