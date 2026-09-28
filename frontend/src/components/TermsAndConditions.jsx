export default function TermsAndConditions() {
  return (
    <div style={{ maxWidth: 760 }}>
      <div className="card">
        <h3 style={{ fontSize: 18, marginBottom: 4 }}>Terms and Conditions</h3>
        <p style={{ fontSize: 12, color: "var(--text-soft)", marginBottom: 20 }}>Last updated: September 2026</p>

        <Section title="Prototype status">
          This application is a working prototype submitted for Smart India Hackathon problem statement
          SIH26009. It is not a certified or production geological survey tool, and it should not be the
          sole basis for a mining, drilling, or investment decision.
        </Section>

        <Section title="Model outputs are estimates">
          Prospectivity scores, reserve ranges, thickness, ore grade, and water table figures produced by
          this application are statistical model outputs, some calibrated against real state or district
          averages and some (thickness, per-point water table depth, per-point grade, social infrastructure
          score) are illustrative estimates rather than direct field measurements, as labeled in the
          application itself. Actual site conditions can differ materially from these estimates. Borehole
          data, CGWB groundwater records, and on-site geological survey remain the authoritative sources for
          any real decision.
        </Section>

        <Section title="Underlying real data">
          Where the application cites production, reserve, or grade figures from the Indian Bureau of Mines
          Yearbook or MOIL disclosures, those figures reflect the published source at the time this
          prototype was built and may not reflect the most current government releases.
        </Section>

        <Section title="Acceptable use">
          Do not use the Upload tab's "replace mine list" mode against a shared or production deployment
          you do not control, since it overwrites the live mine list for every user of that deployment. Do
          not submit personal, confidential, or unlawful content through the Chat tab, since that text is
          sent to a third-party language model API.
        </Section>

        <Section title="No warranty">
          This software is provided as-is, without warranty of any kind, for the purposes of hackathon
          evaluation and demonstration.
        </Section>

        <Section title="Changes">
          These terms may be updated as the prototype evolves during and after the hackathon submission
          period.
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
