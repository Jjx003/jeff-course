<script lang="ts">
  import Header from '$lib/components/Header.svelte';
  import { APP_DESCRIPTION, APP_TAGLINE } from '$lib/config/app.js';

  const features = [
    { kicker: '01', title: 'Courses as files', desc: 'Create or share a track with readable YAML, Markdown, quizzes, drills, and starter code.' },
    { kicker: '02', title: 'Local progress', desc: 'Drafts, completions, study time, and achievements stay in a local DuckDB file.' },
    { kicker: '03', title: 'Practice your way', desc: 'Move between reading, coding, quizzes, tests, and timed drills without changing tools.' },
    { kicker: '04', title: 'Calm momentum', desc: 'Use quiet streaks, useful stats, and a private activity history to keep moving.' }
  ];
</script>

<Header />

<main class="home-main">
  <section class="hero">
    <div class="hero-copy">
      <p class="eyebrow"><span aria-hidden="true"></span>{APP_TAGLINE}</p>
      <h1>Learn deeply.<br /><span>Keep it yours.</span></h1>
      <p class="hero-description">{APP_DESCRIPTION}</p>

      <div class="hero-actions">
        <a href="/tracks" class="btn-primary hero-primary">
          Explore courses
          <svg aria-hidden="true" viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 10h12M11 5l5 5-5 5" /></svg>
        </a>
        <a href="/stats" class="btn-ghost">View progress</a>
      </div>

      <div class="hero-notes" aria-label="Platform highlights">
        <span>Portable course files</span>
        <span>Local-first progress</span>
        <span>Built for any device</span>
      </div>
    </div>

    <div class="hero-visual" aria-hidden="true">
      <div class="visual-glow"></div>
      <div class="course-window">
        <div class="window-bar"><i></i><i></i><i></i><span>course.yaml</span></div>
        <div class="window-body">
          <div class="code-line"><em>title:</em> Introduction to Tensors</div>
          <div class="code-line"><em>difficulty:</em> intermediate</div>
          <div class="code-line"><em>modules:</em></div>
          <div class="module-preview active"><b>01</b><span>Shape and strides</span><i>reading</i></div>
          <div class="module-preview"><b>02</b><span>Build a Tensor class</span><i>coding</i></div>
          <div class="module-preview"><b>03</b><span>Broadcasting</span><i>quiz</i></div>
        </div>
      </div>
    </div>
  </section>

  <section class="feature-section" aria-labelledby="feature-title">
    <div class="section-intro">
      <p>Designed for focused learning</p>
      <h2 id="feature-title">Everything useful. Nothing noisy.</h2>
    </div>
    <div class="feature-grid">
      {#each features as feature}
        <article class="feature-card">
          <span class="feature-number">{feature.kicker}</span>
          <h3>{feature.title}</h3>
          <p>{feature.desc}</p>
        </article>
      {/each}
    </div>
  </section>
</main>

<style>
  .home-main { flex: 1; overflow-y: auto; }
  .hero { position: relative; display: grid; grid-template-columns: minmax(0, 1fr) minmax(360px, 0.82fr); align-items: center; gap: clamp(3rem, 8vw, 7rem); width: min(1160px, calc(100% - 3rem)); min-height: min(660px, calc(100vh - 56px)); margin: 0 auto; padding: 5rem 0 4rem; }
  .hero-copy { position: relative; z-index: 1; }
  .eyebrow { display: flex; align-items: center; gap: 0.65rem; margin: 0 0 1.25rem; color: #93c5fd; font-size: 0.75rem; font-weight: 750; letter-spacing: 0.11em; text-transform: uppercase; }
  .eyebrow span { width: 7px; height: 7px; border-radius: 999px; background: #60a5fa; box-shadow: 0 0 0 5px rgba(96, 165, 250, 0.1); }
  h1 { max-width: 680px; margin: 0; color: #f8fafc; font-size: clamp(3rem, 6vw, 5rem); font-weight: 780; letter-spacing: -0.055em; line-height: 0.98; }
  h1 span { color: #94a3b8; }
  .hero-description { max-width: 590px; margin: 1.6rem 0 0; color: #94a3b8; font-size: clamp(1rem, 1.8vw, 1.15rem); line-height: 1.75; }
  .hero-actions { display: flex; gap: 0.75rem; margin-top: 2rem; }
  .hero-primary { padding-inline: 1.25rem; }
  .hero-notes { display: flex; flex-wrap: wrap; gap: 0.65rem 1.15rem; margin-top: 1.75rem; color: #64748b; font-size: 0.72rem; font-weight: 600; }
  .hero-notes span { display: inline-flex; align-items: center; gap: 0.45rem; }
  .hero-notes span::before { content: ''; width: 3px; height: 3px; border-radius: 999px; background: #475569; }
  .hero-visual { position: relative; }
  .visual-glow { position: absolute; inset: 15% 0; border-radius: 999px; background: rgba(37, 99, 235, 0.18); filter: blur(70px); }
  .course-window { position: relative; overflow: hidden; border: 1px solid rgba(71, 85, 105, 0.72); border-radius: 16px; background: rgba(17, 20, 25, 0.9); box-shadow: 0 30px 80px rgba(0, 0, 0, 0.38), inset 0 1px rgba(255, 255, 255, 0.04); transform: rotate(1.5deg); }
  .window-bar { display: flex; align-items: center; gap: 0.4rem; height: 42px; padding: 0 0.9rem; border-bottom: 1px solid rgba(51, 65, 85, 0.65); color: #64748b; font-family: ui-monospace, monospace; font-size: 0.65rem; }
  .window-bar i { width: 7px; height: 7px; border-radius: 50%; background: #334155; }
  .window-bar span { margin-left: 0.45rem; }
  .window-body { padding: 1.35rem; color: #94a3b8; font-family: ui-monospace, monospace; font-size: 0.72rem; }
  .code-line { margin-bottom: 0.7rem; }
  .code-line em { color: #60a5fa; font-style: normal; }
  .module-preview { display: grid; grid-template-columns: 28px 1fr auto; align-items: center; gap: 0.7rem; margin-top: 0.55rem; padding: 0.75rem; border: 1px solid rgba(51, 65, 85, 0.55); border-radius: 9px; background: rgba(15, 23, 42, 0.34); }
  .module-preview.active { border-color: rgba(96, 165, 250, 0.38); background: rgba(37, 99, 235, 0.08); }
  .module-preview b { color: #64748b; font-size: 0.65rem; }
  .module-preview span { color: #cbd5e1; }
  .module-preview i { color: #64748b; font-size: 0.6rem; font-style: normal; }
  .feature-section { width: min(1160px, calc(100% - 3rem)); margin: 0 auto; padding: 4.5rem 0 6rem; border-top: 1px solid rgba(51, 65, 85, 0.42); }
  .section-intro { margin-bottom: 2rem; }
  .section-intro p { margin: 0 0 0.45rem; color: #60a5fa; font-size: 0.72rem; font-weight: 750; letter-spacing: 0.08em; text-transform: uppercase; }
  .section-intro h2 { margin: 0; color: #e2e8f0; font-size: clamp(1.5rem, 3vw, 2.15rem); letter-spacing: -0.035em; }
  .feature-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; }
  .feature-card { min-height: 190px; padding: 1.25rem; border: 1px solid rgba(51, 65, 85, 0.58); border-radius: 12px; background: rgba(20, 23, 28, 0.72); transition: transform 150ms ease, border-color 150ms ease, background 150ms ease; }
  .feature-card:hover { transform: translateY(-2px); border-color: rgba(96, 165, 250, 0.4); background: rgba(24, 28, 35, 0.92); }
  .feature-number { display: inline-flex; margin-bottom: 2.5rem; color: #60a5fa; font-family: ui-monospace, monospace; font-size: 0.68rem; font-weight: 700; }
  .feature-card h3 { margin: 0 0 0.5rem; color: #e2e8f0; font-size: 0.9rem; }
  .feature-card p { margin: 0; color: #64748b; font-size: 0.78rem; line-height: 1.65; }
  @media (max-width: 900px) { .hero { grid-template-columns: 1fr; gap: 3rem; padding-top: 4rem; } .hero-visual { max-width: 560px; } .feature-grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 560px) { .hero, .feature-section { width: min(100% - 2rem, 1160px); } .hero { align-items: start; min-height: auto; padding-top: 3rem; } h1 { font-size: 3rem; } .hero-actions { align-items: stretch; flex-direction: column; } .feature-grid { grid-template-columns: 1fr; } .feature-card { min-height: auto; } .feature-number { margin-bottom: 1.5rem; } }
</style>
