export default function PrivacyPolicy() {
  return (
    <div style={{ maxWidth: 760 }}>
      <div className="card">
        <h3 style={{ fontSize: 18, marginBottom: 4 }}>Privacy Policy</h3>
        <p style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 20 }}>Last updated: September 2026</p>

        <Section title="What this application is">
          This is a prototype built for Smart India Hackathon submission SIH26009 (Manganese Intelligence
          Platform). It does not have user accounts, sign-in, or persistent user profiles. There is nothing
          to register for and nothing tied to an individual identity.
        </Section>

        <Section title="Data this application uses">
          The mine, production, reserve and grade figures shown come from published sources: the Indian
          Bureau of Mines Yearbook, MOIL public disclosures, and government reserve/production tables.
          Site coordinates you enter (on the Map or Upload tabs) are used only to query satellite imagery
          (via Google Earth Engine) and run the prospectivity model, then returned to you in the response.
          These coordinates are not stored on our servers beyond the lifetime of that single request, aside
          from the zone-scoring cache described below.
        </Section>

        <Section title="Chat messages">
          Text you send on the Chat tab is forwarded to Groq's API (which runs an open-weight language
          model) to generate a reply, along with results from internal data-lookup tools the assistant
          calls on your behalf. Do not enter personal or confidential information in chat messages, since
          this text leaves our server to be processed by that third-party API. Chat history is kept only in
          your browser's memory for the current session; closing or reloading the page clears it.
        </Section>

        <Section title="Local cache">
          To avoid recomputing the same map grid repeatedly, scored zone results (coordinates and model
          output, no personal data) are cached as files on the server for a limited area. This cache holds
          no information about who requested it.
        </Section>

        <Section title="Uploaded CSV files">
          Files you upload on the Upload tab are read in memory to score coordinates or replace the demo
          mine list, and are not retained after the request completes, except that a mine-list replacement
          can optionally be written to the server's local mine list file if you tick "persist to disk."
        </Section>

        <Section title="Cookies and tracking">
          This application does not use cookies, analytics scripts, or third-party trackers.
        </Section>

        <Section title="Third-party services in use">
          Google Earth Engine (satellite imagery), Groq (chat model inference). Each operates under its own
          privacy terms for the specific request it processes.
        </Section>

        <Section title="Contact">
          This is a hackathon prototype without a dedicated support address. Questions about this
          submission should go through the SIH26009 team channel.
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <h4 style={{ fontSize: 14, marginBottom: 6 }}>{title}</h4>
      <p style={{ fontSize: 13, color: "var(--text-soft)", lineHeight: 1.6 }}>{children}</p>
    </div>
  );
}
