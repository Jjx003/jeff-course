<script lang="ts">
  import { APP_NAME } from '$lib/config/app.js';

  interface User {
    id: string;
    name: string;
    role: 'admin' | 'learner';
  }

  interface Props {
    data: { next: string; users: User[]; currentUserId: string | null };
    form?: { error?: string };
  }

  let { data, form }: Props = $props();

  const tones = ['tone-blue', 'tone-green', 'tone-amber', 'tone-rose', 'tone-violet', 'tone-cyan'];

  function initials(name: string): string {
    return name.split(/\s+/).slice(0, 2).map((part) => part[0]?.toUpperCase() ?? '').join('');
  }
</script>

<main class="profile-page">
  <section class="profile-shell">
    <p class="brand">{APP_NAME}</p>
    <h1>Who is learning?</h1>
    <p class="subtitle">Choose a profile to keep progress and practice history separate.</p>

    {#if form?.error}
      <p class="error-message">{form.error}</p>
    {/if}

    <div class="profile-grid">
      {#each data.users as user, index}
        <form method="POST" action={`/auth/sign-in?next=${encodeURIComponent(data.next)}`}>
          <input type="hidden" name="userId" value={user.id} />
          <button class="profile-choice" type="submit" aria-label={`Continue as ${user.name}`}>
            <span class="avatar {tones[index % tones.length]}" class:current={user.id === data.currentUserId}>
              {initials(user.name)}
            </span>
            <span class="profile-name">{user.name}</span>
            {#if user.id === data.currentUserId}<span class="current-label">Current</span>{/if}
          </button>
        </form>
      {/each}
    </div>

    <a class="manage-link" href="/auth/users">Manage profiles</a>
  </section>
</main>

<style>
  .profile-page {
    min-height: 100dvh;
    overflow-y: auto;
    padding: 3rem 1.5rem;
    background: #020617;
    color: #f8fafc;
  }
  .profile-shell {
    width: 100%;
    max-width: 58rem;
    margin: 0 auto;
    text-align: center;
  }
  .brand {
    margin-bottom: 2.5rem;
    color: #60a5fa;
    font-size: 0.9rem;
    font-weight: 800;
  }
  h1 {
    font-size: clamp(2rem, 7vw, 3rem);
    font-weight: 750;
    line-height: 1.1;
  }
  .subtitle {
    margin: 0.75rem auto 2.5rem;
    color: #94a3b8;
    font-size: 0.95rem;
  }
  .error-message {
    max-width: 28rem;
    margin: 0 auto 1.5rem;
    padding: 0.65rem 0.85rem;
    border: 1px solid #881337;
    border-radius: 6px;
    background: rgb(76 5 25 / 0.35);
    color: #fecdd3;
  }
  .profile-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(8.5rem, 1fr));
    gap: 1.5rem;
    max-width: 46rem;
    margin: 0 auto;
  }
  .profile-choice {
    display: flex;
    width: 100%;
    flex-direction: column;
    align-items: center;
    border: 0;
    background: transparent;
    color: inherit;
    cursor: pointer;
  }
  .avatar {
    display: grid;
    width: 7rem;
    aspect-ratio: 1;
    place-items: center;
    border: 3px solid transparent;
    border-radius: 8px;
    color: #fff;
    font-size: 2rem;
    font-weight: 800;
    transition: border-color 150ms, transform 150ms;
  }
  .profile-choice:hover .avatar,
  .avatar.current {
    border-color: #f8fafc;
    transform: translateY(-2px);
  }
  .profile-name {
    margin-top: 0.75rem;
    color: #cbd5e1;
    font-size: 0.95rem;
    font-weight: 650;
  }
  .current-label {
    margin-top: 0.2rem;
    color: #60a5fa;
    font-size: 0.7rem;
    font-weight: 700;
  }
  .tone-blue { background: #2563eb; }
  .tone-green { background: #059669; }
  .tone-amber { background: #d97706; }
  .tone-rose { background: #e11d48; }
  .tone-violet { background: #7c3aed; }
  .tone-cyan { background: #0891b2; }
  .manage-link {
    display: inline-flex;
    margin-top: 2.75rem;
    padding: 0.55rem 0.9rem;
    border: 1px solid #475569;
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 0.85rem;
    font-weight: 650;
    text-decoration: none;
  }
  .manage-link:hover {
    border-color: #94a3b8;
    color: #fff;
  }
</style>
