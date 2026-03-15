---
layout: default
title: Agency Agents Catalog
---

<div class="hero">
  <div class="container">
    <h1 class="hero-title">Agency Agents</h1>
    <p class="hero-subtitle">A comprehensive catalog of specialized AI agents for software development, design, marketing, and more.</p>

    <div class="search-container">
      <label for="search-input" class="visually-hidden">Search agents by name or description</label>
      <input type="text" id="search-input" class="search-input" placeholder="Search agents by name or description..." aria-describedby="search-hint">
      <span class="search-icon" aria-hidden="true">🔍</span>
      <span id="search-hint" class="visually-hidden">Type to filter agents by name or description</span>
    </div>

    <div class="filter-bar">
      <div class="category-filters" role="group" aria-label="Filter agents by category">
        <button class="filter-btn active" data-category="all" aria-pressed="true">All</button>
        {% for category in site.data.categories %}
        <button class="filter-btn" data-category="{{ category.id }}" aria-pressed="false">{{ category.name_en }}</button>
        {% endfor %}
      </div>
      <button id="favorites-btn" class="favorites-btn" aria-pressed="false" aria-label="Show favorites">
        ⭐ Favorites
      </button>
    </div>
  </div>
</div>

<div class="container">
  <div class="agents-grid" id="agents-grid" role="list" aria-label="Agent listings">
    {% for agent in site.data.agents %}
    <a href="{{ agent.url }}" class="agent-card" role="listitem" data-category="{{ agent.category }}" data-name="{{ agent.name | downcase | escape }}" data-description="{{ agent.description_en | downcase | replace: '"', '&quot;' }} {{ agent.description_zh | downcase | replace: '"', '&quot;' }}">
      <button class="favorite-btn" data-agent="{{ agent.name | downcase | escape }}" aria-label="Add to favorites" onclick="toggleFavorite('{{ agent.name | downcase | escape }}', event)">☆</button>
      <div class="card-header" style="background-color: {{ agent.color }}20;">
        <span class="card-emoji" aria-hidden="true">{{ agent.emoji }}</span>
      </div>
      <div class="card-body">
        <span class="card-category">{{ agent.category_name }}</span>
        <h3 class="card-title">{{ agent.name }}</h3>
        <p class="card-description" lang="en">{{ agent.description_en }}</p>
        <p class="card-description zh-only" lang="zh">{{ agent.description_zh }}</p>
      </div>
    </a>
    {% endfor %}
  </div>

  <div class="no-results" id="no-results" style="display: none;" role="status" aria-live="polite">
    <div class="no-results-content">
      <span class="no-results-icon" aria-hidden="true">🔍</span>
      <h3 class="no-results-title">No agents found</h3>
      <p class="no-results-text">Try adjusting your search or filter to find what you're looking for.</p>
    </div>
  </div>
</div>

<script>
  // Pass agents data to JavaScript
  window.agentsData = {{ site.data.agents | jsonify }};
  window.categoriesData = {{ site.data.categories | jsonify }};
</script>
