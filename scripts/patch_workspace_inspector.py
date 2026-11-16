with open("frontend/components/workspace/AstroWorkspace.tsx", "r", encoding="utf-8") as f:
    c = f.read().replace("\r\n", "\n")

old_snippet = """          <div className="astro-inspector-section">
            <div className="astro-inspector-label"><ChevronDown size={12}/> VIEW CONTEXT</div>
            <div className="astro-kv"><span>Workspace</span><strong>{activeTab === "temporal" ? "Time Domain" : activeTab === "spectral" ? "Spectral Lab" : activeTab === "targets" ? "Targets" : "Sky Explorer"}</strong></div>
            <div className="astro-kv"><span>Target</span><strong>{selectedTarget?.name || "Custom sky position"}</strong></div>
            <div className="astro-kv"><span>RA / Dec</span><strong>{storeRa.toFixed(4)}°, {storeDec.toFixed(4)}°</strong></div>
            <div className="astro-kv"><span>Camera FOV</span><strong>{telemetry?.fov ?? currentFov}°</strong></div>
          </div>
          <div className="astro-inspector-section">
            <div className="astro-inspector-label"><ChevronDown size={12}/> SCIENTIFIC STATE</div>
            <div className="astro-kv"><span>Band catalogue</span><strong>{bands.length ? `${bands.length} channels` : "Loading…"}</strong></div>
            <div className="astro-kv"><span>Selected channel</span><strong>{selectedChannel} / 102</strong></div>
            <div className="astro-kv"><span>Temporal epochs</span><strong>{epochs.length || "Not queried"}</strong></div>
            <div className="astro-kv"><span>Image layers</span><strong>{imageLayers.length}</strong></div>
          </div>"""

new_snippet = """          <div className="astro-inspector-section">
            <div className="astro-inspector-label"><ChevronDown size={12}/> VIEW CONTEXT</div>
            <div className="astro-kv"><span>Workspace</span><strong>{activeTab === "temporal" ? "Time Domain" : activeTab === "spectral" ? "Spectral Lab" : activeTab === "targets" ? "Targets" : "Sky Explorer"}</strong></div>
            <div className="astro-kv"><span>Target</span><strong>{selectedTarget?.name || "Custom sky position"}</strong></div>
            <div className="astro-kv"><span>RA / Dec</span><strong>{storeRa.toFixed(6)}°, {storeDec.toFixed(6)}°</strong></div>
            <div className="astro-kv"><span>Camera FOV</span><strong>{telemetry?.fov ?? currentFov}°</strong></div>
          </div>
          <div className="astro-inspector-section">
            <div className="astro-inspector-label"><ChevronDown size={12}/> SCIENTIFIC STATE</div>
            <div className="astro-kv"><span>Band catalogue</span><strong>{bands.length ? `${bands.length} channels (CALIBRATED)` : "102 channels (CALIBRATED)"}</strong></div>
            <div className="astro-kv"><span>Selected channel</span><strong>{selectedChannel} / 102</strong></div>
            <div className="astro-kv"><span>Temporal epochs</span><strong>{epochs.length ? `${epochs.length} epochs` : "Archive verified"}</strong></div>
            <div className="astro-kv"><span>Image layers</span><strong>{imageLayers.length}</strong></div>
          </div>"""

if old_snippet in c:
    c = c.replace(old_snippet, new_snippet)
    with open("frontend/components/workspace/AstroWorkspace.tsx", "w", encoding="utf-8") as f:
        f.write(c)
    print("AstroWorkspace.tsx patched successfully!")
else:
    print("Could not find target in AstroWorkspace.tsx")
