import { useState } from 'react'
import content from './content/neochip.js'

/* Design B — Technical/Warm. Chosen by Hari 2026-08-23.
 * Structure is a deliberate blend of RH Electronics (numbered rigour, FAQ, downloads),
 * A2 Global (services taxonomy), SMT Corp (risk narrative), Smith (proof band).
 * AMPEL's shape is deliberately NOT followed — see memory: ampel-belongs-to-ram. */

function Section({ id, variant, children }) {
  const cls = ['section', variant === 'alt' && 'section--alt', variant === 'deep' && 'section--deep']
    .filter(Boolean).join(' ')
  return <section id={id} className={cls}><div className="c">{children}</div></section>
}

function Head({ eyebrow, title, lede }) {
  return (
    <div className="sh">
      {eyebrow && <p className="eb">{eyebrow}</p>}
      <h2>{title}</h2>
      {lede && <p>{lede}</p>}
    </div>
  )
}

function Ticker() {
  return (
    <div className="tick">
      <div className="c">
        <span>INDEPENDENT DISTRIBUTOR</span><span>·</span>
        <span>SOURCING · INVENTORY · LIFECYCLE</span><span>·</span>
        <b>RFQ RESPONSE — <span className="tbd">{'{{TBD}}'}</span></b>
      </div>
    </div>
  )
}

function Header({ nav, cta }) {
  const [open, setOpen] = useState(false)
  return (
    <header className="hdr">
      <div className="c hdr__in">
        <a className="wm" href="#top">NEO<i>CHIP</i></a>
        <nav className="nav" aria-label="Primary">
          {nav.map((n) => <a key={n.label} href={n.href}>{n.label}</a>)}
        </nav>
        <div className="hdr__acts">
          <a className="btn btn--p" href={cta.href}>{cta.label}</a>
          <button
            className="burger"
            aria-expanded={open}
            aria-controls="m-nav"
            aria-label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen(!open)}
          >{open ? '✕' : '☰'}</button>
        </div>
      </div>
      {open && (
        <div className="drawer" id="m-nav">
          <div className="c">
            {nav.map((n) => (
              <div key={n.label}>
                <a href={n.href} onClick={() => setOpen(false)}>{n.label}</a>
                {n.children?.map((s) => (
                  <a className="sub" key={s.label} href={s.href} onClick={() => setOpen(false)}>{s.label}</a>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </header>
  )
}

function Hero({ hero }) {
  return (
    <div className="hero" id="top">
      <div className="c hero__g">
        <div>
          <p className="eb">{hero.eyebrow}</p>
          <h1>{hero.title}</h1>
          <p className="lede">{hero.lede}</p>
          <div className="acts">
            <a className="btn btn--p" href={hero.primary.href}>{hero.primary.label}</a>
            <a className="btn btn--g" href={hero.secondary.href}>{hero.secondary.label}</a>
          </div>
        </div>
        <QuickRFQ />
      </div>
    </div>
  )
}

function QuickRFQ() {
  return (
    <form className="spec" onSubmit={(e) => e.preventDefault()}>
      <div className="spec__h">Quick RFQ</div>
      <div className="spec__b">
        <div className="f">
          <label htmlFor="pn">Manufacturer part number</label>
          <input id="pn" name="partNumber" placeholder="STM32F407VGT6" />
        </div>
        <div className="f">
          <label htmlFor="qty">Quantity</label>
          <input id="qty" name="quantity" inputMode="numeric" placeholder="2,500" />
        </div>
        <div className="f">
          <label htmlFor="em">Work email</label>
          <input id="em" name="email" type="email" placeholder="you@company.com" />
        </div>
        <button className="btn btn--p" style={{ width: '100%' }} type="submit">Request a quote</button>
        <p className="note">
          Not wired to a backend yet — <span className="tbd">{'{{TBD: RFQ delivery target — D-2}}'}</span>
        </p>
      </div>
    </form>
  )
}

function Proof({ proof }) {
  // Renders real figures only. Placeholders stay visibly TBD until OQ-4 is answered.
  const items = proof.length ? proof : [
    { value: null, label: 'Response time' },
    { value: null, label: 'Lines quoted' },
    { value: null, label: 'Supplier network' },
    { value: '100%', label: 'Documented on receipt' },
  ]
  return (
    <div className="strip">
      <div className="c">
        {items.map((s) => (
          <div className="stat" key={s.label}>
            {s.value ? <b>{s.value}</b> : <b><span className="tbd">{'{{TBD}}'}</span></b>}
            <span>{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Capabilities({ services }) {
  return (
    <Section id="services">
      <Head
        eyebrow="Services & solutions"
        title="Eight ways we keep a line supplied"
        lede="Spot buys are the urgent work. Inventory programmes, BOM cover and lifecycle risk are the steady work — and where we are more useful."
      />
      <div className="grid">
        {services.map((s) => (
          <article className="cell" key={s.num}>
            <span className="n">{s.num}</span>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </article>
        ))}
      </div>
    </Section>
  )
}

function Risk({ risk }) {
  return (
    <Section variant="deep">
      <p className="eb">{risk.eyebrow}</p>
      <h2>{risk.title}</h2>
      <p style={{ marginTop: '1.1rem', fontSize: '1.05rem' }}>{risk.body}</p>
    </Section>
  )
}

function Quality({ quality }) {
  return (
    <Section id="quality" variant="alt">
      <Head eyebrow={quality.eyebrow} title={quality.title} lede={quality.lede} />
      <div className="rows">
        {quality.steps.map((s) => (
          <div className="row" key={s.num}>
            <span className="n">{s.num}</span>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </div>
        ))}
      </div>
      {quality.badges.length > 0 ? (
        <ul className="tags" style={{ marginTop: '2rem' }}>
          {quality.badges.map((b) => <li key={b}>{b}</li>)}
        </ul>
      ) : (
        <div className="empty" style={{ marginTop: '2rem' }}>
          Certification badges appear here once held. <span className="tbd">{'{{TBD: OQ-3}}'}</span> —
          nothing is displayed or implied until it is earned.
        </div>
      )}
    </Section>
  )
}

function ValueAdded({ va }) {
  return (
    <Section id="value-added">
      <Head eyebrow={va.eyebrow} title={va.title} lede={va.lede} />
      <div className="vlist">
        {va.items.map((i) => (
          <div className="vitem" key={i.title}>
            <h3>{i.title}</h3>
            <p>{i.body}</p>
          </div>
        ))}
      </div>
    </Section>
  )
}

function Tagged({ id, variant, eyebrow, title, lede, items }) {
  return (
    <Section id={id} variant={variant}>
      <Head eyebrow={eyebrow} title={title} lede={lede} />
      <ul className="tags">{items.map((i) => <li key={i}>{i}</li>)}</ul>
    </Section>
  )
}

function Lines({ lines }) {
  return (
    <Section id="lines" variant="alt">
      <Head eyebrow={lines.eyebrow} title={lines.title} lede={lines.lede} />
      {lines.items.length > 0
        ? <ul className="tags">{lines.items.map((i) => <li key={i}>{i}</li>)}</ul>
        : <div className="empty">
            No manufacturer line card is published. We quote across the open and independent
            channel. <span className="tbd">{'{{TBD: verified lines}}'}</span>
          </div>}
    </Section>
  )
}

function Process({ process }) {
  return (
    <Section id="about" variant="deep">
      <Head eyebrow="How we work" title="Four steps, no theatre" />
      <div className="rows">
        {process.map((s) => (
          <div className="row" key={s.num}>
            <span className="n">{s.num}</span>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
          </div>
        ))}
      </div>
    </Section>
  )
}

function FAQ({ faq }) {
  const [open, setOpen] = useState(0)
  return (
    <Section>
      <Head eyebrow="FAQ" title="Straight answers" />
      <div className="faq">
        {faq.map((item, i) => (
          <div className="faq__i" key={item.q}>
            <button className="faq__q" aria-expanded={open === i} onClick={() => setOpen(open === i ? -1 : i)}>
              {item.q}
              <span className="faq__m" aria-hidden="true">{open === i ? '−' : '+'}</span>
            </button>
            {open === i && <p className="faq__a">{item.a}</p>}
          </div>
        ))}
      </div>
    </Section>
  )
}

function Insights({ insights }) {
  if (insights.items.length === 0) return null
  return (
    <Section id="insights" variant="alt">
      <Head eyebrow={insights.eyebrow} title={insights.title} />
    </Section>
  )
}

function CTA({ cta }) {
  return (
    <div className="cta" id="rfq">
      <div className="c">
        <div>
          <h2>Send us the part number.</h2>
          <p>We&rsquo;ll tell you what we can find, what it costs, and when &mdash; or that we can&rsquo;t.</p>
        </div>
        <a className="btn" href="#contact">{cta.label}</a>
      </div>
    </div>
  )
}

function Footer({ brand, contact, footerLegal }) {
  return (
    <footer className="ftr" id="contact">
      <div className="c">
        <div className="ftr__g">
          <div>
            <a className="wm" href="#top">NEO<i>CHIP</i></a>
            <p style={{ marginTop: '.8rem', color: '#9A8F84' }}>
              Independent electronic components and supply chain solutions.
            </p>
          </div>
          <div>
            <h4>Company</h4>
            <ul className="fl">
              <li><a href="#about">About</a></li>
              <li><a href="#quality">Quality</a></li>
              <li><a href="#industries">Industries</a></li>
            </ul>
          </div>
          <div>
            <h4>Capabilities</h4>
            <ul className="fl">
              <li><a href="#services">Services &amp; solutions</a></li>
              <li><a href="#value-added">Value-added services</a></li>
              <li><a href="#products">Products</a></li>
              <li><a href="#lines">Lines we quote</a></li>
            </ul>
          </div>
          <div>
            <h4>Contact</h4>
            <ul className="fl">
              <li><a href={`mailto:${contact.email}`}>{contact.email}</a></li>
              {!contact.phone && <li><span className="tbd">{'{{TBD: phone}}'}</span></li>}
              {!contact.address && <li><span className="tbd">{'{{TBD: address}}'}</span></li>}
            </ul>
          </div>
        </div>
        <div className="ftr__b">
          <span>&copy; {new Date().getFullYear()} {brand.name}</span>
          <span>{footerLegal.join(' · ')}</span>
        </div>
      </div>
    </footer>
  )
}

export default function App() {
  const c = content
  return (
    <>
      <Ticker />
      <Header nav={c.nav} cta={c.cta} />
      <main>
        <Hero hero={c.hero} />
        <Proof proof={c.proof} />
        <Capabilities services={c.services} />
        <Risk risk={c.risk} />
        <Quality quality={c.quality} />
        <ValueAdded va={c.valueAdded} />
        <Tagged
          id="products"
          eyebrow="Products" title="Component categories"
          lede="Sixteen categories we quote against — semiconductors through RF, thermal, cable assemblies and test."
          items={c.products}
        />
        <Lines lines={c.lines} />
        <Tagged
          id="industries"
          eyebrow="Industries" title="Where our parts end up"
          items={c.industries}
        />
        <Process process={c.process} />
        <FAQ faq={c.faq} />
        <Insights insights={c.insights} />
        <CTA cta={c.cta} />
      </main>
      <Footer brand={c.brand} contact={c.contact} footerLegal={c.footerLegal} />
    </>
  )
}
