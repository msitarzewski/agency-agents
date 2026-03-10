import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/drisk_dev',
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : undefined,
});

async function main() {
  const client = await pool.connect();
  try {
    console.log('Seeding Assessment Templates and Questions...');

    // Need to insert template first
    const templateRes = await client.query(`
      INSERT INTO assessment_templates (name, version, tier, is_active)
      VALUES ('Standard Site Assessment', '1.0', 2, true)
      ON CONFLICT (name, version) DO UPDATE SET is_active = EXCLUDED.is_active
      RETURNING id;
    `);
    const templateId = templateRes.rows[0].id;

    // Domains
    const domains = [
      { num: 1, name: 'Site Context', desc: 'General site characteristics' },
      { num: 2, name: 'Asset Criticality', desc: 'Critical assets on site' },
      { num: 3, name: 'External Threat Context', desc: 'Threats from the outside' },
      { num: 4, name: 'Physical Protection', desc: 'Physical security of site' },
      { num: 5, name: 'Access Governance', desc: 'Access control procedures' },
      { num: 6, name: 'Human and Procedural Controls', desc: 'Guarding & procedures' },
      { num: 7, name: 'Response Capability', desc: 'How site responds to incidents' },
      { num: 8, name: 'Insider and Role-Based Exposure', desc: 'Insider risks' },
      { num: 9, name: 'Resilience and Recovery', desc: 'BCP and recovery' },
      { num: 10, name: 'Compliance and Assurance', desc: 'Documentation & audits' },
    ];

    for (const d of domains) {
      const domRes = await client.query(`
        INSERT INTO assessment_domains (template_id, name, domain_number, description)
        SELECT $1, $2, $3, $4
        WHERE NOT EXISTS (
          SELECT 1 FROM assessment_domains WHERE template_id = $1 AND domain_number = $3
        )
        RETURNING id;
      `, [templateId, d.name, d.num, d.desc]);

      let domainId;
      if (domRes.rowCount && domRes.rowCount > 0) {
        domainId = domRes.rows[0].id;
      } else {
        const fetchRes = await client.query(`SELECT id FROM assessment_domains WHERE template_id = $1 AND domain_number = $2`, [templateId, d.num]);
        domainId = fetchRes.rows[0].id;
      }

      // Provide ~50 core questions strictly mapped to domains
      const allQuestions: Record<number, Array<{text: string, weight: number}>> = {
        1: [
          { text: "Primary function of site?", weight: 1 },
          { text: "Is site publicly accessible?", weight: 2 },
          { text: "Does site accommodate vulnerable persons?", weight: 4 },
          { text: "Are critical services delivered from this site?", weight: 3 },
          { text: "Are there any high-profile or sensitive operations on site?", weight: 3 }
        ],
        2: [
          { text: "Are there critical server or data rooms?", weight: 4 },
          { text: "Are medicines or dangerous goods stored securely?", weight: 4 },
          { text: "Is there cash or high-value stock on site?", weight: 3 },
          { text: "Are master keys or access credentials stored safely?", weight: 4 },
          { text: "Are there essential infrastructure components (e.g., generators, switch rooms)?", weight: 3 }
        ],
        3: [
          { text: "Located in high-crime or disorder area?", weight: 3 },
          { text: "Is trespass or ASB evident?", weight: 2 },
          { text: "Is site isolated during low occupancy?", weight: 3 },
          { text: "Is there a history of protest or disorder near the site?", weight: 3 },
          { text: "Is the site easily approachable by hostile vehicles?", weight: 4 }
        ],
        4: [
          { text: "Is perimeter clearly defined and secured?", weight: 3 },
          { text: "Are entry points physically secure?", weight: 3 },
          { text: "Is CCTV installed at key areas?", weight: 2 },
          { text: "Is external lighting sufficient to support deterrence and visibility?", weight: 2 },
          { text: "Are windows, glazing, and shutters robust against forced entry?", weight: 3 }
        ],
        5: [
          { text: "Is there a visitor management process?", weight: 2 },
          { text: "Are access credentials controlled and reviewed?", weight: 4 },
          { text: "Are restricted areas clearly defined?", weight: 3 },
          { text: "Are access cards, fobs, keys, or credentials issued and withdrawn under controlled procedures?", weight: 4 },
          { text: "Are contractor access rights properly vetted and managed?", weight: 3 }
        ],
        6: [
          { text: "Are security patrols structured and recorded?", weight: 2 },
          { text: "Are opening and closing procedures documented?", weight: 2 },
          { text: "Are incidents recorded and escalated properly?", weight: 3 },
          { text: "Are officers briefed and aware of current threats?", weight: 3 },
          { text: "Is lone worker protection adequate?", weight: 4 }
        ],
        7: [
          { text: "Is there a clear incident response plan?", weight: 3 },
          { text: "Are response times appropriate for the site risk level?", weight: 4 },
          { text: "Are communication systems reliable?", weight: 4 },
          { text: "Is there clear command and escalation clarity?", weight: 3 },
          { text: "Are first response and mobile response arrangements effective?", weight: 3 }
        ],
        8: [
          { text: "Are privileged access rights restricted?", weight: 4 },
          { text: "Are master keys and critical credentials controlled?", weight: 4 },
          { text: "Is there lone access to critical spaces?", weight: 3 },
          { text: "Is there segregation of duties to prevent insider compromise?", weight: 3 },
          { text: "Is vetting alignment appropriate for roles?", weight: 4 }
        ],
        9: [
          { text: "Are backup arrangements in place for critical systems?", weight: 4 },
          { text: "Are alternative operating arrangements documented?", weight: 3 },
          { text: "Are there clear restoration readiness plans?", weight: 3 },
          { text: "Is the site tolerant to power or telecommunications outages?", weight: 3 },
          { text: "Is there a heavy reliance on critical suppliers?", weight: 2 }
        ],
        10: [
          { text: "Is there a current site risk assessment?", weight: 4 },
          { text: "Are audit actions tracked to completion?", weight: 3 },
          { text: "Is there evidence of ongoing security review?", weight: 2 },
          { text: "Are training records and policy alignment up to date?", weight: 2 },
          { text: "Are there regular drills or exercise history?", weight: 2 }
        ]
      };

      const domainQuestions = allQuestions[d.num] || [];
      for (let i = 0; i < domainQuestions.length; i++) {
        const qData = domainQuestions[i];
        await client.query(`
          INSERT INTO assessment_questions (domain_id, question_text, question_number, weight, answer_options, sort_order)
          SELECT $1::uuid, $2::text, $3::varchar, $4::integer, $5::jsonb, $6::integer
          WHERE NOT EXISTS (
            SELECT 1 FROM assessment_questions WHERE domain_id = $1 AND question_number = $3
          )
        `, [
          domainId,
          qData.text,
          `${d.num}.${i+1}`,
          qData.weight,
          JSON.stringify([
            { label: 'Yes / Fully / Low Risk', score: 1 },
            { label: 'Partially / Medium Risk', score: 3 },
            { label: 'No / None / High Risk', score: 5 },
          ]),
          i + 1
        ]);
      }
    }
    
    console.log('Template, Domains, and Questions sorted!');
  } catch (error) {
    console.error(error);
  } finally {
    client.release();
    pool.end();
  }
}

main();
