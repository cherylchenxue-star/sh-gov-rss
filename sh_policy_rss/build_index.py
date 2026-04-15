#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成交互式 index.html 预览页面
"""

import json
from datetime import datetime
from typing import List

from sh_policy_rss.models import PolicyItem


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>上海政策 RSS 聚合</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css">
  <link rel="alternate" type="application/rss+xml" title="上海政策RSS聚合" href="{rss_link}">
  <style>
    .line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .line-clamp-3 { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
  </style>
</head>
<body class="bg-gray-50 min-h-screen">
  <div id="app" class="max-w-5xl mx-auto px-4 py-6 sm:py-8">
    <!-- Header -->
    <header class="mb-6">
      <h1 class="text-2xl sm:text-3xl font-bold text-slate-800 mb-2">上海政策 RSS 聚合</h1>
      <p class="text-slate-600 mb-4 text-sm sm:text-base">自动抓取上海市经信委、发改委、科委等政府部门的政策通知。</p>
      <div class="flex flex-wrap gap-3">
        <a id="rss-btn" href="{rss_link}" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition min-h-[44px]">
          <i class="fa fa-rss mr-2"></i>订阅 RSS
        </a>
        <button type="button" id="refresh-btn" class="inline-flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition min-h-[44px]">
          <i class="fa fa-refresh mr-2" id="refresh-icon"></i>刷新数据
        </button>
        <a href="https://github.com/cherylchenxue-star/sh-gov-rss" class="inline-flex items-center px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-900 transition min-h-[44px]">
          <i class="fa fa-github mr-2"></i>GitHub 仓库
        </a>
      </div>
    </header>

    <!-- Stats Bar -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-4">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div class="flex items-center gap-3 flex-wrap">
          <span class="text-slate-700 font-medium">共 <span id="stat-total" class="text-blue-600 font-bold">{total}</span> 条政策</span>
          <span class="text-slate-400 hidden sm:inline">|</span>
          <span class="text-sm text-slate-500">更新时间：<span id="stat-updated">{updated_at}</span></span>
        </div>
        <div id="source-badges" class="flex flex-wrap gap-2">
          <!-- badges injected by JS -->
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-4 sticky top-0 z-30">
      <div class="flex flex-col gap-3">
        <div class="relative flex-1">
          <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
          <input id="search-input" type="text" placeholder="搜索标题、摘要、来源..." class="w-full pl-10 pr-9 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base">
          <button id="search-clear" class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 hidden" aria-label="清除搜索">
            <i class="fa fa-times-circle"></i>
          </button>
        </div>
        <div class="flex flex-wrap gap-2 pb-1 sm:pb-0">
          <div class="relative">
            <button type="button" id="source-dropdown-btn" class="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 active:bg-gray-100 flex items-center gap-2 min-h-[44px] whitespace-nowrap cursor-pointer select-none">
              来源<i class="fa fa-chevron-down text-xs text-gray-400 pointer-events-none"></i>
              <span id="source-badge" class="ml-1 bg-blue-600 text-white text-xs px-1.5 rounded-full hidden pointer-events-none">0</span>
            </button>
            <div id="source-dropdown-panel" class="hidden absolute left-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-2 min-w-[200px] z-40">
              <div class="max-h-64 overflow-y-auto" id="source-options">
                <!-- checkboxes injected by JS -->
              </div>
              <div class="border-t border-gray-100 mt-2 pt-2 flex gap-2">
                <button type="button" id="source-select-all" class="flex-1 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded cursor-pointer">全选</button>
                <button type="button" id="source-clear" class="flex-1 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded cursor-pointer">清空</button>
              </div>
            </div>
          </div>

          <div class="relative">
            <button type="button" id="tag-dropdown-btn" class="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 active:bg-gray-100 flex items-center gap-2 min-h-[44px] whitespace-nowrap cursor-pointer select-none">
              标签<i class="fa fa-chevron-down text-xs text-gray-400 pointer-events-none"></i>
              <span id="tag-badge" class="ml-1 bg-blue-600 text-white text-xs px-1.5 rounded-full hidden pointer-events-none">0</span>
            </button>
            <div id="tag-dropdown-panel" class="hidden absolute left-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-2 min-w-[200px] z-40">
              <div class="space-y-1 max-h-64 overflow-y-auto" id="tag-options">
                <!-- tag buttons injected by JS -->
              </div>
            </div>
          </div>

          <div class="relative">
            <button type="button" id="date-dropdown-btn" class="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 active:bg-gray-100 flex items-center gap-2 min-h-[44px] whitespace-nowrap cursor-pointer select-none">
              日期<i class="fa fa-chevron-down text-xs text-gray-400 pointer-events-none"></i>
            </button>
            <div id="date-dropdown-panel" class="hidden absolute left-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-2 min-w-[200px] z-40">
              <div class="space-y-1">
                <button type="button" data-value="all" class="date-option w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm cursor-pointer">全部时间</button>
                <button type="button" data-value="7d" class="date-option w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm cursor-pointer">近7天</button>
                <button type="button" data-value="30d" class="date-option w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm cursor-pointer">近30天</button>
                <button type="button" data-value="90d" class="date-option w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm cursor-pointer">近90天</button>
                <div class="border-t border-gray-100 pt-2 mt-1">
                  <div class="px-3 py-1 text-xs text-gray-500">自定义</div>
                  <div class="flex gap-2 px-3 py-1">
                    <input id="custom-start" type="date" class="border border-gray-200 rounded px-2 py-1 text-sm w-full">
                    <span class="text-gray-400 self-center">-</span>
                    <input id="custom-end" type="date" class="border border-gray-200 rounded px-2 py-1 text-sm w-full">
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="relative">
            <button type="button" id="sort-dropdown-btn" class="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 active:bg-gray-100 flex items-center gap-2 min-h-[44px] whitespace-nowrap cursor-pointer select-none">
              排序<i class="fa fa-chevron-down text-xs text-gray-400 pointer-events-none"></i>
            </button>
            <div id="sort-dropdown-panel" class="hidden absolute left-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-2 min-w-[140px] z-40">
              <button type="button" data-value="desc" class="sort-option w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm bg-blue-50 text-blue-700 cursor-pointer">日期倒序</button>
              <button type="button" data-value="asc" class="sort-option w-full text-left px-3 py-2 rounded hover:bg-gray-100 text-sm cursor-pointer">日期正序</button>
            </div>
          </div>

          <button type="button" id="reset-btn" class="px-3 py-2 text-gray-600 hover:bg-gray-100 active:bg-gray-200 border border-gray-200 rounded-lg min-h-[44px] whitespace-nowrap cursor-pointer select-none">
            <i class="fa fa-refresh mr-1"></i>重置
          </button>
        </div>
      </div>

      <!-- Active Filters -->
      <div id="active-filters" class="hidden flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-gray-100">
        <span class="text-xs text-gray-500">已筛选：</span>
        <div id="active-filters-list" class="flex flex-wrap gap-2"></div>
        <button id="clear-all-filters" class="text-xs text-gray-500 hover:text-gray-700 underline ml-auto">清除全部</button>
      </div>
    </div>

    <!-- Policy List -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div class="px-4 sm:px-6 py-3 border-b border-gray-100 flex items-center justify-between">
        <h2 class="font-semibold text-slate-800 text-sm sm:text-base">最新政策</h2>
        <span id="result-count" class="text-sm text-slate-500"></span>
      </div>
      <ul id="policy-list" class="divide-y divide-gray-100">
        <!-- items injected by JS -->
      </ul>
      <div id="load-more-container" class="px-4 py-4 border-t border-gray-100 text-center hidden">
        <button id="load-more-btn" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition min-h-[44px]">加载更多</button>
      </div>
    </div>

    <!-- Empty State -->
    <div id="empty-state" class="hidden py-16 text-center">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
        <i class="fa fa-search text-2xl text-gray-400"></i>
      </div>
      <h3 class="text-lg font-medium text-slate-700 mb-1">未找到匹配的政策</h3>
      <p class="text-sm text-slate-500 mb-4">请尝试调整筛选条件或更换搜索关键词</p>
      <button id="empty-clear-btn" class="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition border border-blue-200">清除全部筛选</button>
    </div>

    <!-- Footer -->
    <footer class="mt-8 text-center text-sm text-slate-500">
      <p class="mb-2">数据来源：上海市经信委、上海市经信委专项资金、上海市发改委、上海市科委</p>
      <p class="flex justify-center gap-4">
        <a href="{rss_link}" class="hover:text-blue-600">RSS 订阅</a>
        <a href="https://github.com/cherylchenxue-star/sh-gov-rss" class="hover:text-slate-800">GitHub 仓库</a>
      </p>
    </footer>
  </div>

  <script>
    window.POLICY_DATA = {policy_data_json};
  </script>
  <script>
    (function() {
      const data = window.POLICY_DATA;

      const state = {
        filters: {
          search: '',
          sources: data.sources.map(s => s.id),
          tag: 'all',
          dateRange: 'all',
          customStart: '',
          customEnd: '',
        },
        sort: 'desc',
        pagination: {
          page: 1,
          pageSize: 20,
        },
      };

      function debounce(fn, ms) {
        let t;
        return function(...args) {
          clearTimeout(t);
          t = setTimeout(() => fn.apply(this, args), ms);
        };
      }

      function formatDateLabel(range) {
        const map = { 'all': '全部时间', '7d': '近7天', '30d': '近30天', '90d': '近90天', 'custom': '自定义' };
        return map[range] || range;
      }

      function getFilteredPolicies() {
        return data.policies.filter(p => {
          if (!state.filters.sources.includes(p.sourceId)) return false;
          if (state.filters.tag !== 'all' && !p.tags.includes(state.filters.tag)) return false;
          if (state.filters.dateRange !== 'all') {
            const policyDate = new Date(p.date);
            const now = new Date();
            if (state.filters.dateRange === 'custom') {
              if (state.filters.customStart && policyDate < new Date(state.filters.customStart)) return false;
              if (state.filters.customEnd && policyDate > new Date(state.filters.customEnd)) return false;
            } else {
              const days = { '7d': 7, '30d': 30, '90d': 90 }[state.filters.dateRange];
              const cutoff = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
              cutoff.setHours(0,0,0,0);
              if (policyDate < cutoff) return false;
            }
          }
          if (state.filters.search) {
            const q = state.filters.search.toLowerCase();
            const text = (p.title + ' ' + p.source + ' ' + p.summary + ' ' + p.tags.join(' ')).toLowerCase();
            if (!text.includes(q)) return false;
          }
          return true;
        }).sort((a, b) => {
          const da = new Date(a.date), db = new Date(b.date);
          return state.sort === 'desc' ? db - da : da - db;
        });
      }

      function renderStats() {
        const badgeContainer = document.getElementById('source-badges');
        badgeContainer.innerHTML = '';
        data.sources.forEach(s => {
          const count = data.policies.filter(p => p.sourceId === s.id).length;
          if (count > 0) {
            const badge = document.createElement('span');
            badge.className = 'inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700 border border-gray-200';
            badge.textContent = s.name + ' ' + count;
            badgeContainer.appendChild(badge);
          }
        });
      }

      function renderSourceDropdown() {
        const container = document.getElementById('source-options');
        container.innerHTML = '';
        data.sources.forEach(s => {
          const label = document.createElement('label');
          label.className = 'flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer rounded';
          label.innerHTML = `<input type="checkbox" value="${s.id}" class="source-checkbox w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500" ${state.filters.sources.includes(s.id) ? 'checked' : ''}> <span class="text-sm text-gray-700">${s.name}</span>`;
          container.appendChild(label);
        });
      }

      function renderTagDropdown() {
        const container = document.getElementById('tag-options');
        container.innerHTML = '';
        const allBtn = document.createElement('button');
        allBtn.className = 'tag-option w-full text-left px-3 py-2 rounded text-sm ' + (state.filters.tag === 'all' ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-100');
        allBtn.textContent = '全部标签';
        allBtn.dataset.value = 'all';
        container.appendChild(allBtn);
        data.allTags.forEach(tag => {
          const btn = document.createElement('button');
          btn.className = 'tag-option w-full text-left px-3 py-2 rounded text-sm ' + (state.filters.tag === tag ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-100');
          btn.textContent = tag;
          btn.dataset.value = tag;
          container.appendChild(btn);
        });
      }

      function renderActiveFilters() {
        const container = document.getElementById('active-filters');
        const list = document.getElementById('active-filters-list');
        list.innerHTML = '';
        let hasAny = false;

        if (state.filters.search) {
          hasAny = true;
          list.appendChild(createFilterTag('搜索: ' + state.filters.search, () => { state.filters.search = ''; document.getElementById('search-input').value = ''; renderAll(); }));
        }
        const isPartialSourceFilter = state.filters.sources.length > 0 && state.filters.sources.length < data.sources.length;
        if (isPartialSourceFilter) {
          hasAny = true;
          const sourceNames = state.filters.sources.map(id => {
            const s = data.sources.find(x => x.id === id);
            return s ? s.name : id;
          });
          list.appendChild(createFilterTag('来源: ' + sourceNames.join('、'), () => {
            state.filters.sources = data.sources.map(s => s.id);
            renderSourceDropdown();
            renderAll();
          }));
        }
        if (state.filters.tag !== 'all') {
          hasAny = true;
          list.appendChild(createFilterTag('标签: ' + state.filters.tag, () => { state.filters.tag = 'all'; renderTagDropdown(); renderAll(); }));
        }
        if (state.filters.dateRange !== 'all') {
          hasAny = true;
          let label = formatDateLabel(state.filters.dateRange);
          if (state.filters.dateRange === 'custom' && (state.filters.customStart || state.filters.customEnd)) {
            label += ' (' + (state.filters.customStart || '') + ' ~ ' + (state.filters.customEnd || '') + ')';
          }
          list.appendChild(createFilterTag(label, () => { state.filters.dateRange = 'all'; document.getElementById('custom-start').value = ''; document.getElementById('custom-end').value = ''; renderAll(); }));
        }

        container.classList.toggle('hidden', !hasAny);
        const sourceBadge = document.getElementById('source-badge');
        sourceBadge.textContent = state.filters.sources.length;
        sourceBadge.classList.toggle('hidden', !isPartialSourceFilter);
        const tagBadge = document.getElementById('tag-badge');
        tagBadge.textContent = state.filters.tag === 'all' ? '0' : '1';
        tagBadge.classList.toggle('hidden', state.filters.tag === 'all');
      }

      function createFilterTag(text, onRemove) {
        const span = document.createElement('span');
        span.className = 'inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full';
        span.innerHTML = `<span>${text}</span><button class="hover:text-blue-900 leading-none" aria-label="移除"><i class="fa fa-times"></i></button>`;
        span.querySelector('button').addEventListener('click', onRemove);
        return span;
      }

      function renderPolicyList() {
        const filtered = getFilteredPolicies();
        const sorted = filtered;
        const pageSize = state.pagination.page * state.pagination.pageSize;
        const paginated = sorted.slice(0, pageSize);
        const hasMore = sorted.length > paginated.length;

        const listEl = document.getElementById('policy-list');
        listEl.innerHTML = '';

        document.getElementById('result-count').textContent = `共 ${sorted.length} 条`;
        document.getElementById('empty-state').classList.toggle('hidden', paginated.length > 0);
        document.getElementById('load-more-container').classList.toggle('hidden', !hasMore);

        if (paginated.length === 0) return;

        paginated.forEach(item => {
          const li = document.createElement('li');
          li.className = 'px-4 sm:px-6 py-4 hover:bg-gray-50 transition';
          const summary = item.summary || '';
          const summaryHtml = summary ? `<p class="text-sm text-slate-600 line-clamp-2 sm:line-clamp-3 mt-1">${escapeHtml(summary)}</p>` : '';
          const tagsHtml = (item.tags && item.tags.length) ? `<div class="flex flex-wrap gap-1 mt-1">${item.tags.map(t => `<span class="tag-pill cursor-pointer inline-flex items-center px-2 py-0.5 rounded text-xs bg-emerald-50 text-emerald-700 border border-emerald-100 hover:bg-emerald-100 transition" data-tag="${escapeHtml(t)}">${escapeHtml(t)}</span>`).join('')}</div>` : '';
          li.innerHTML = `
            <div class="flex flex-col gap-1">
              <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1 sm:gap-2">
                <a href="${item.link}" target="_blank" class="text-base font-medium text-slate-800 hover:text-blue-600 transition line-clamp-2">${escapeHtml(item.title)}</a>
                <span class="text-sm text-slate-400 whitespace-nowrap shrink-0">${item.date}</span>
              </div>
              <div class="flex items-center gap-2 text-sm">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700 border border-blue-100">${escapeHtml(item.source)}</span>
              </div>
              ${summaryHtml}
              ${tagsHtml}
            </div>
          `;
          listEl.appendChild(li);
        });
        // Bind tag click events
        listEl.querySelectorAll('.tag-pill').forEach(pill => {
          pill.addEventListener('click', () => {
            state.filters.tag = pill.dataset.tag;
            state.pagination.page = 1;
            renderTagDropdown();
            renderAll();
          });
        });
      }

      function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
      }

      function renderAll() {
        renderStats();
        renderActiveFilters();
        renderPolicyList();
      }

      function showToast(message, type = 'success') {
        let toast = document.getElementById('page-toast');
        if (!toast) {
          toast = document.createElement('div');
          toast.id = 'page-toast';
          toast.className = 'fixed top-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg shadow-lg text-sm font-medium z-50 transition-opacity duration-300 opacity-0';
          document.body.appendChild(toast);
        }
        toast.className = 'fixed top-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg shadow-lg text-sm font-medium z-50 transition-opacity duration-300 ' + (type === 'success' ? 'bg-emerald-600 text-white' : 'bg-red-600 text-white');
        toast.textContent = message;
        toast.style.opacity = '1';
        setTimeout(() => { toast.style.opacity = '0'; }, 2500);
      }

      async function refreshFromRSS() {
        const icon = document.getElementById('refresh-icon');
        icon.classList.add('fa-spin');
        try {
          const res = await fetch(data.rssLink + '?t=' + Date.now());
          if (!res.ok) throw new Error('HTTP ' + res.status);
          const xmlText = await res.text();
          const parser = new DOMParser();
          const doc = parser.parseFromString(xmlText, 'application/xml');
          const parserError = doc.querySelector('parsererror');
          if (parserError) throw new Error('XML parse error');

          const sourceNameToId = {};
          data.sources.forEach(s => sourceNameToId[s.name] = s.id);

          const items = Array.from(doc.querySelectorAll('item'));
          const policies = [];
          const allTags = new Set();

          items.forEach(item => {
            const title = item.querySelector('title')?.textContent?.trim() || '';
            const link = item.querySelector('link')?.textContent?.trim() || '';
            const pubDate = item.querySelector('pubDate')?.textContent?.trim() || '';
            const description = item.querySelector('description')?.textContent?.trim() || '';
            const sourceName = item.querySelector('source')?.textContent?.trim() || '';

            let summary = '';
            const brIdx = description.indexOf('<br/>');
            if (brIdx !== -1) {
              summary = description.slice(brIdx + 5).trim();
            } else if (description.startsWith('来源:')) {
              const lines = description.split(/[\\n\\r]+/);
              summary = lines.slice(1).join(' ').trim();
            } else {
              summary = description;
            }

            const d = new Date(pubDate);
            const dateStr = isNaN(d) ? '' : d.toISOString().slice(0, 10);

            const tags = Array.from(item.querySelectorAll('category')).map(c => c.textContent.trim()).filter(Boolean);
            tags.forEach(t => allTags.add(t));

            policies.push({
              id: link + '-' + hashCode(title),
              title,
              link,
              date: dateStr,
              sourceId: sourceNameToId[sourceName] || '',
              source: sourceName,
              summary,
              tags,
            });
          });

          data.policies = policies;
          data.allTags = Array.from(allTags).sort();
          data.meta.totalCount = policies.length;
          data.meta.updatedAt = new Date().toLocaleString('zh-CN', { hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replace(/\\//g, '-');

          state.filters.sources = data.sources.map(s => s.id);
          state.filters.tag = 'all';
          state.filters.dateRange = 'all';
          state.filters.search = '';
          state.pagination.page = 1;

          document.getElementById('search-input').value = '';
          document.getElementById('search-clear').classList.add('hidden');
          document.getElementById('custom-start').value = '';
          document.getElementById('custom-end').value = '';

          renderTagDropdown();
          updateDateDropdownUI();
          updateSortDropdownUI();
          renderAll();
          showToast('数据已刷新', 'success');
        } catch (e) {
          console.error(e);
          showToast('刷新失败：' + (e.message || '无法加载 RSS'), 'error');
        } finally {
          icon.classList.remove('fa-spin');
        }
      }

      function hashCode(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
          const char = str.charCodeAt(i);
          hash = ((hash << 5) - hash) + char;
          hash = hash & hash;
        }
        return hash;
      }

      function bindEvents() {
        const searchInput = document.getElementById('search-input');
        const searchClear = document.getElementById('search-clear');
        const sourceBtn = document.getElementById('source-dropdown-btn');
        const sourcePanel = document.getElementById('source-dropdown-panel');
        const tagBtn = document.getElementById('tag-dropdown-btn');
        const tagPanel = document.getElementById('tag-dropdown-panel');
        const dateBtn = document.getElementById('date-dropdown-btn');
        const datePanel = document.getElementById('date-dropdown-panel');
        const sortBtn = document.getElementById('sort-dropdown-btn');
        const sortPanel = document.getElementById('sort-dropdown-panel');

        function closeAllPanels(except) {
          if (except !== 'source') sourcePanel.classList.add('hidden');
          if (except !== 'tag') tagPanel.classList.add('hidden');
          if (except !== 'date') datePanel.classList.add('hidden');
          if (except !== 'sort') sortPanel.classList.add('hidden');
        }

        searchInput.addEventListener('input', debounce(() => {
          state.filters.search = searchInput.value.trim();
          state.pagination.page = 1;
          searchClear.classList.toggle('hidden', !state.filters.search);
          renderAll();
        }, 200));
        searchClear.addEventListener('click', () => {
          searchInput.value = '';
          state.filters.search = '';
          searchClear.classList.add('hidden');
          state.pagination.page = 1;
          renderAll();
        });

        sourceBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const willShow = sourcePanel.classList.contains('hidden');
          closeAllPanels();
          if (willShow) sourcePanel.classList.remove('hidden');
        });
        document.getElementById('source-options').addEventListener('change', (e) => {
          if (e.target.classList.contains('source-checkbox')) {
            const val = e.target.value;
            if (e.target.checked) {
              if (!state.filters.sources.includes(val)) state.filters.sources.push(val);
            } else {
              state.filters.sources = state.filters.sources.filter(id => id !== val);
            }
            state.pagination.page = 1;
            renderAll();
          }
        });
        document.getElementById('source-select-all').addEventListener('click', () => {
          state.filters.sources = data.sources.map(s => s.id);
          renderSourceDropdown();
          state.pagination.page = 1;
          renderAll();
        });
        document.getElementById('source-clear').addEventListener('click', () => {
          state.filters.sources = [];
          renderSourceDropdown();
          state.pagination.page = 1;
          renderAll();
        });

        tagBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const willShow = tagPanel.classList.contains('hidden');
          closeAllPanels();
          if (willShow) tagPanel.classList.remove('hidden');
        });
        document.getElementById('tag-options').addEventListener('click', (e) => {
          if (e.target.classList.contains('tag-option')) {
            state.filters.tag = e.target.dataset.value;
            state.pagination.page = 1;
            renderTagDropdown();
            renderAll();
          }
        });

        dateBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const willShow = datePanel.classList.contains('hidden');
          closeAllPanels();
          if (willShow) datePanel.classList.remove('hidden');
        });
        datePanel.querySelectorAll('.date-option').forEach(btn => {
          btn.addEventListener('click', () => {
            state.filters.dateRange = btn.dataset.value;
            if (state.filters.dateRange !== 'custom') {
              document.getElementById('custom-start').value = '';
              document.getElementById('custom-end').value = '';
              state.filters.customStart = '';
              state.filters.customEnd = '';
            }
            state.pagination.page = 1;
            renderAll();
            updateDateDropdownUI();
          });
        });
        document.getElementById('custom-start').addEventListener('change', (e) => {
          state.filters.dateRange = 'custom';
          state.filters.customStart = e.target.value;
          state.pagination.page = 1;
          renderAll();
          updateDateDropdownUI();
        });
        document.getElementById('custom-end').addEventListener('change', (e) => {
          state.filters.dateRange = 'custom';
          state.filters.customEnd = e.target.value;
          state.pagination.page = 1;
          renderAll();
          updateDateDropdownUI();
        });

        sortBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const willShow = sortPanel.classList.contains('hidden');
          closeAllPanels();
          if (willShow) sortPanel.classList.remove('hidden');
        });
        sortPanel.querySelectorAll('.sort-option').forEach(btn => {
          btn.addEventListener('click', () => {
            state.sort = btn.dataset.value;
            state.pagination.page = 1;
            renderAll();
            updateSortDropdownUI();
          });
        });

        document.addEventListener('click', () => {
          closeAllPanels();
        });

        // Reset
        document.getElementById('reset-btn').addEventListener('click', () => {
          state.filters.search = '';
          state.filters.sources = data.sources.map(s => s.id);
          state.filters.tag = 'all';
          state.filters.dateRange = 'all';
          state.filters.customStart = '';
          state.filters.customEnd = '';
          state.sort = 'desc';
          state.pagination.page = 1;
          searchInput.value = '';
          searchClear.classList.add('hidden');
          document.getElementById('custom-start').value = '';
          document.getElementById('custom-end').value = '';
          renderSourceDropdown();
          renderTagDropdown();
          updateDateDropdownUI();
          updateSortDropdownUI();
          renderAll();
        });

        // Clear all filters
        document.getElementById('clear-all-filters').addEventListener('click', () => {
          state.filters.search = '';
          state.filters.sources = data.sources.map(s => s.id);
          state.filters.tag = 'all';
          state.filters.dateRange = 'all';
          state.filters.customStart = '';
          state.filters.customEnd = '';
          state.pagination.page = 1;
          searchInput.value = '';
          searchClear.classList.add('hidden');
          document.getElementById('custom-start').value = '';
          document.getElementById('custom-end').value = '';
          renderSourceDropdown();
          renderTagDropdown();
          updateDateDropdownUI();
          renderAll();
        });

        document.getElementById('empty-clear-btn').addEventListener('click', () => {
          document.getElementById('clear-all-filters').click();
        });

        // Refresh
        document.getElementById('refresh-btn').addEventListener('click', () => {
          refreshFromRSS();
        });

        // Load more
        document.getElementById('load-more-btn').addEventListener('click', () => {
          state.pagination.page += 1;
          renderPolicyList();
        });
      }

      function updateDateDropdownUI() {
        document.querySelectorAll('.date-option').forEach(btn => {
          const active = btn.dataset.value === state.filters.dateRange;
          btn.className = 'date-option w-full text-left px-3 py-2 rounded text-sm ' + (active ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-100');
        });
      }

      function updateSortDropdownUI() {
        document.querySelectorAll('.sort-option').forEach(btn => {
          const active = btn.dataset.value === state.sort;
          btn.className = 'sort-option w-full text-left px-3 py-2 rounded text-sm ' + (active ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-100');
        });
      }

      renderSourceDropdown();
      renderTagDropdown();
      bindEvents();
      renderAll();
    })();
  </script>
</body>
</html>
"""

def build_index(items: List[PolicyItem]) -> str:
    total = len(items)
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    rss_link = "./上海政策rss.xml"

    sorted_items = sorted(items, key=lambda x: x.pub_date, reverse=True)

    sources = []
    source_ids = sorted(set(item.source_id for item in items))
    for sid in source_ids:
        name = next((i.source for i in items if i.source_id == sid), sid)
        count = sum(1 for i in items if i.source_id == sid)
        sources.append({"id": sid, "name": name, "count": count})

    policies = []
    for item in sorted_items:
        policies.append({
            "id": f"{item.source_id}-{hash(item.link)}",
            "title": item.title,
            "link": item.link,
            "date": item.pub_date.strftime("%Y-%m-%d"),
            "sourceId": item.source_id,
            "source": item.source,
            "summary": item.summary or "",
            "tags": item.tags,
        })

    all_tags = sorted(set(tag for item in items for tag in item.tags))

    policy_data = {
        "meta": {
            "updatedAt": updated_at,
            "totalCount": total,
        },
        "sources": sources,
        "allTags": all_tags,
        "rssLink": rss_link,
        "policies": policies,
    }

    policy_data_json = json.dumps(policy_data, ensure_ascii=False, separators=(",", ":"))

    html = HTML_TEMPLATE
    html = html.replace("{total}", str(total))
    html = html.replace("{updated_at}", updated_at)
    html = html.replace("{rss_link}", rss_link)
    html = html.replace("{policy_data_json}", policy_data_json)
    return html
