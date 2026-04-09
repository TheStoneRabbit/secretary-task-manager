#!/usr/bin/env python3
"""
Visualize task deadlines and priorities
Generates an HTML dashboard showing what's due when
"""

import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from config import get_base_dir

# HTML template with embedded CSS and JS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Deadline Dashboard</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📋</text></svg>">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #00356B;
            font-size: 36px;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: #666;
            font-size: 16px;
        }
        
        .search-container {
            margin-top: 20px;
            position: relative;
        }
        
        .search-box {
            width: 100%;
            padding: 15px 50px 15px 20px;
            font-size: 16px;
            border: 2px solid #E5E7EB;
            border-radius: 12px;
            transition: all 0.3s;
            font-family: inherit;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .search-icon {
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: #9CA3AF;
            font-size: 20px;
            pointer-events: none;
        }
        
        .search-results-count {
            margin-top: 10px;
            color: #6B7280;
            font-size: 14px;
            font-style: italic;
        }
        
        .search-results-container {
            margin-top: 20px;
            display: none;
        }
        
        .search-results-container.active {
            display: block;
        }
        
        .search-results-header {
            font-size: 18px;
            font-weight: bold;
            color: #00356B;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #E5E7EB;
        }
        
        .hidden {
            display: none !important;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-results-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            display: none;
        }
        
        .stat-results-container.active {
            display: block;
            animation: fadeIn 0.3s ease-in;
        }
        
        .stat-results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #E5E7EB;
        }
        
        .stat-results-title {
            color: #00356B;
            font-size: 24px;
            font-weight: bold;
        }
        
        .close-stat-results {
            background: #667eea;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: white;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .close-stat-results:hover {
            background: #5568d3;
            transform: translateX(-3px);
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .stat-card.active {
            border: 2px solid #667eea;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .stat-number {
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .stat-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-card.urgent .stat-number { color: #EF4444; }
        .stat-card.today .stat-number { color: #F59E0B; }
        .stat-card.this-week .stat-number { color: #3B82F6; }
        .stat-card.blocked .stat-number { color: #8B5CF6; }
        .stat-card.completed .stat-number { color: #10B981; }
        .stat-card.past-events .stat-number { color: #6B7280; }
        
        .stat-filter-button {
            margin-top: 10px;
            background: #F3F4F6;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
            color: #6B7280;
            transition: all 0.2s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }
        
        .stat-filter-button:hover {
            background: #10B981;
            color: white;
            transform: translateY(-2px);
        }
        
        .stat-filter-button.active {
            background: #10B981;
            color: white;
        }
        
        .timeline-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .timeline-section h2 {
            color: #00356B;
            margin-bottom: 25px;
            font-size: 24px;
        }
        
        .day-details-container {
            display: none;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            animation: fadeIn 0.3s ease-in;
        }
        
        .day-details-container.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .day-details-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #E5E7EB;
        }
        
        .day-details-title {
            color: #00356B;
            font-size: 24px;
            font-weight: bold;
        }
        
        .close-details {
            background: #F3F4F6;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            color: #6B7280;
            transition: all 0.2s;
        }
        
        .close-details:hover {
            background: #E5E7EB;
            color: #374151;
        }
        
        .day-section {
            margin-bottom: 30px;
        }
        
        .day-header {
            font-size: 18px;
            font-weight: bold;
            color: #00356B;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 3px solid #E5E7EB;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .day-count {
            background: #F3F4F6;
            color: #666;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: normal;
        }
        
        .task-card {
            background: #F9FAFB;
            border-left: 4px solid #3B82F6;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .task-card:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .task-card.priority-high { border-left-color: #EF4444; }
        .task-card.priority-medium { border-left-color: #F59E0B; }
        .task-card.priority-low { border-left-color: #10B981; }
        .task-card.blocked { 
            border-left-color: #8B5CF6; 
            background: #FAF5FF;
        }
        .task-card.personal-meeting {
            border-left-color: #EC4899;
            background: #FDF2F8;
        }
        
        .task-title {
            font-size: 16px;
            font-weight: 600;
            color: #1F2937;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }
        .copy-task-btn {
            flex-shrink: 0;
            padding: 2px 10px;
            border-radius: 6px;
            border: 1px solid #D1D5DB;
            background: #F9FAFB;
            color: #6B7280;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            opacity: 0;
        }
        .task-card:hover .copy-task-btn {
            opacity: 1;
        }
        .copy-task-btn:hover {
            background: #E5E7EB;
            color: #374151;
            border-color: #9CA3AF;
        }
        .date-filter-bar {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
            padding: 10px 16px;
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            font-size: 14px;
            color: #6B7280;
        }
        .date-filter-bar label {
            font-weight: 500;
            white-space: nowrap;
        }
        .date-filter-input {
            padding: 6px 10px;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            font-size: 14px;
            font-family: inherit;
            color: #374151;
        }
        .date-filter-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .date-filter-sep {
            color: #9CA3AF;
        }
        .date-filter-btn {
            padding: 6px 16px;
            border-radius: 6px;
            border: 1px solid #667eea;
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .date-filter-btn:hover {
            background: rgba(102, 126, 234, 0.2);
        }
        .date-filter-btn.clear {
            border-color: #EF4444;
            color: #EF4444;
            background: rgba(239, 68, 68, 0.05);
        }
        .date-filter-btn.clear:hover {
            background: rgba(239, 68, 68, 0.15);
        }

        .task-card.meeting-completed {
            opacity: 0.6;
            border-left-color: #10B981;
        }
        .task-badge.completed-meeting {
            background: #D1FAE5;
            color: #065F46;
        }
        
        .task-meta {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            font-size: 13px;
            color: #6B7280;
        }
        
        .task-badge {
            background: #E5E7EB;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .task-badge.project { background: #DBEAFE; color: #1E40AF; }
        .task-badge.blocked { background: #EDE9FE; color: #6B21A8; }
        .task-badge.urgent { background: #FEE2E2; color: #991B1B; }
        .task-badge.personal { background: #FCE7F3; color: #BE185D; }
        
        .past-events-section .day-header {
            color: #6B7280;
            border-bottom-color: #D1D5DB;
        }
        .past-events-section .task-card {
            opacity: 0.7;
            border-left-color: #9CA3AF;
        }
        .past-events-toggle {
            text-align: center;
            margin: 20px 0;
        }
        .past-events-toggle button {
            background: #F3F4F6;
            border: 1px solid #D1D5DB;
            color: #6B7280;
            padding: 10px 24px;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .past-events-toggle button:hover {
            background: #E5E7EB;
            color: #374151;
        }

        .no-tasks {
            text-align: center;
            padding: 40px;
            color: #9CA3AF;
            font-style: italic;
        }
        
        .refresh-notice {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }
        
        /* Timeline Widget Styles */
        .timeline-widget {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            overflow: hidden;
        }
        
        .timeline-widget h2 {
            color: #00356B;
            margin-bottom: 25px;
            font-size: 24px;
        }
        
        .timeline-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        
        .timeline-nav {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .timeline-nav-button {
            background: #F3F4F6;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.2s;
            color: #374151;
        }
        
        .timeline-nav-button:hover:not(:disabled) {
            background: #E5E7EB;
            transform: translateY(-2px);
        }
        
        .timeline-nav-button:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }
        
        .timeline-week-label {
            font-size: 14px;
            color: #6B7280;
            font-weight: 500;
            min-width: 120px;
            text-align: center;
        }
        
        .timeline-scroll-container {
            overflow-x: auto;
            overflow-y: hidden;
            padding: 20px 0;
            margin: 0 -10px;
        }
        
        .timeline-track {
            display: flex;
            gap: 15px;
            min-width: max-content;
            padding: 0 10px;
            position: relative;
        }
        
        .timeline-day {
            min-width: 140px;
            background: #F9FAFB;
            border-radius: 12px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
            position: relative;
        }
        
        .timeline-day:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            border-color: #286DC0;
        }
        
        .timeline-day.today {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .timeline-day.today .timeline-date {
            color: white;
        }
        
        .timeline-day.today .timeline-count {
            background: rgba(255,255,255,0.3);
            color: white;
        }
        
        .timeline-day.selected {
            border-color: #00356B;
            background: #DBEAFE;
        }
        
        .timeline-date {
            font-size: 14px;
            font-weight: bold;
            color: #00356B;
            margin-bottom: 8px;
        }
        
        .timeline-weekday {
            font-size: 12px;
            color: #6B7280;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .timeline-day.today .timeline-weekday {
            color: rgba(255,255,255,0.9);
        }
        
        .timeline-indicators {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .timeline-count {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 11px;
            background: #E5E7EB;
            padding: 4px 8px;
            border-radius: 10px;
            color: #374151;
            font-weight: 600;
        }
        
        .timeline-count.meetings {
            background: #DBEAFE;
            color: #1E40AF;
        }
        
        .timeline-count.tasks {
            background: #FEE2E2;
            color: #991B1B;
        }
        
        .timeline-empty {
            color: #9CA3AF;
            font-size: 12px;
            font-style: italic;
        }
        
        .timeline-day.today .timeline-empty {
            color: rgba(255,255,255,0.8);
        }
        
        /* Scroll hint */
        .scroll-hint {
            text-align: center;
            color: #9CA3AF;
            font-size: 13px;
            margin-top: 10px;
        }
        
        .scroll-hint::after {
            content: '← Scroll →';
            display: block;
            margin-top: 5px;
            font-weight: 600;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr 1fr;
            }
            
            .header h1 {
                font-size: 28px;
            }
        }
    </style>
    <script>
        function scrollToDay(dateId, dayLabel) {
            const element = document.getElementById(dateId);
            const detailsContainer = document.getElementById('day-details-container');
            const detailsContent = document.getElementById('day-details-content');
            const detailsTitle = document.getElementById('day-details-title');
            
            if (element && detailsContainer && detailsContent) {
                // Remove previous selection
                document.querySelectorAll('.timeline-day').forEach(day => {
                    day.classList.remove('selected');
                });
                
                // Add selection to clicked day
                const timelineDay = document.querySelector(`[data-date="${dateId}"]`);
                if (timelineDay) {
                    timelineDay.classList.add('selected');
                }
                
                // Clone the day section content
                const dayContent = element.cloneNode(true);
                dayContent.removeAttribute('id'); // Remove ID to avoid duplicates
                
                // Update details container
                detailsTitle.textContent = dayLabel || element.querySelector('.day-header span')?.textContent || 'Day Details';
                detailsContent.innerHTML = '';
                detailsContent.appendChild(dayContent);
                
                // Show the details container
                detailsContainer.classList.add('active');
                
                // Scroll to details container
                detailsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        
        function closeDayDetails() {
            const detailsContainer = document.getElementById('day-details-container');
            if (detailsContainer) {
                detailsContainer.classList.remove('active');
                
                // Remove selection from timeline
                document.querySelectorAll('.timeline-day').forEach(day => {
                    day.classList.remove('selected');
                });
            }
        }
        
        // Search functionality
        function performSearch() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const resultsContainer = document.getElementById('searchResultsContainer');
            const resultsContent = document.getElementById('searchResultsContent');
            const resultsCount = document.getElementById('searchResultsCount');
            const timelineWidget = document.querySelector('.timeline-widget');
            const dayDetailsContainer = document.getElementById('day-details-container');
            
            if (searchTerm === '') {
                // Clear search - hide results and show timeline widget
                resultsContainer.classList.remove('active');
                resultsContent.innerHTML = '';
                resultsCount.textContent = '';
                
                // Show timeline widget
                if (timelineWidget) {
                    timelineWidget.style.display = '';
                    timelineWidget.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                
                // Keep day details as-is (don't force show/hide)
                return;
            }
            
            // Collect all matching tasks (use a Set to track unique tasks by title to avoid duplicates)
            const seenTasks = new Set();
            const matchingTasks = [];
            let totalMatches = 0;
            
            // Search through timeline sections only (not the details view)
            const daySections = document.querySelectorAll('.timeline-section .day-section');
            
            daySections.forEach(daySection => {
                const dayHeader = daySection.querySelector('.day-header span')?.textContent || '';
                const tasksInDay = daySection.querySelectorAll('.task-card');
                
                tasksInDay.forEach(card => {
                    const title = card.querySelector('.task-title')?.textContent || '';
                    const titleLower = title.toLowerCase();
                    const meta = card.querySelector('.task-meta')?.textContent.toLowerCase() || '';
                    const badges = Array.from(card.querySelectorAll('.task-badge')).map(b => b.textContent.toLowerCase()).join(' ');
                    const details = card.querySelector('.meeting-details')?.textContent.toLowerCase() || '';
                    
                    const searchableText = titleLower + ' ' + meta + ' ' + badges + ' ' + details;
                    
                    // Check if matches and not already added
                    if (searchableText.includes(searchTerm) && !seenTasks.has(title)) {
                        seenTasks.add(title);
                        matchingTasks.push({
                            card: card.cloneNode(true),
                            dayHeader: dayHeader
                        });
                        totalMatches++;
                    }
                });
            });
            
            // Also search past events from JSON data
            const pastEventsData = {past_events_json};
            pastEventsData.forEach(evt => {
                const searchableText = (evt.title + ' ' + (evt.start_time || '') + ' ' + (evt.details || []).join(' ')).toLowerCase();
                if (searchableText.includes(searchTerm) && !seenTasks.has(evt.title + evt.date)) {
                    seenTasks.add(evt.title + evt.date);
                    const dateObj = new Date(evt.date + 'T12:00:00');
                    const dayName = '📜 ' + dateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
                    const card = document.createElement('div');
                    card.className = 'task-card priority-high meeting-completed';
                    let timeStr = evt.start_time ? '⏰ ' + evt.start_time + ' - ' + evt.end_time + ': ' : '';
                    let detailsHtml = '';
                    if (evt.details && evt.details.length > 0) {
                        detailsHtml = '<div class="meeting-details" style="margin-top:8px;">';
                        evt.details.forEach(d => {
                            if (d.includes('[') && d.includes('](')) {
                                const match = d.match(/\[(.+?)\]\((.+?)\)/);
                                if (match) {
                                    detailsHtml += '<div>' + d.replace(match[0], '<a href="' + match[2] + '" target="_blank">' + match[1] + '</a>') + '</div>';
                                } else {
                                    detailsHtml += '<div>' + d + '</div>';
                                }
                            } else {
                                detailsHtml += '<div>' + d + '</div>';
                            }
                        });
                        detailsHtml += '</div>';
                    }
                    card.innerHTML = '<div class="task-title">' + timeStr + evt.title + '</div>' + detailsHtml +
                        '<div class="task-badges"><span class="task-badge">📅 Meeting</span><span class="task-badge completed-meeting">✅ COMPLETED</span></div>';
                    matchingTasks.push({
                        card: card,
                        dayHeader: dayName
                    });
                    totalMatches++;
                }
            });

            // Display results
            if (matchingTasks.length === 0) {
                resultsCount.textContent = `No results found for "${searchTerm}"`;
                resultsContainer.classList.remove('active');
                // Show timeline widget
                if (timelineWidget) {
                    timelineWidget.style.display = '';
                }
            } else {
                // Hide timeline widget to show search results
                if (timelineWidget) {
                    timelineWidget.style.display = 'none';
                }
                
                // Build search results view
                resultsContent.innerHTML = '';
                
                // Add header
                const searchHeader = document.createElement('div');
                searchHeader.className = 'search-results-header';
                searchHeader.textContent = `🔍 Search Results for "${searchTerm}"`;
                resultsContent.appendChild(searchHeader);
                
                // Group by day
                const dayGroups = {};
                matchingTasks.forEach(match => {
                    if (!dayGroups[match.dayHeader]) {
                        dayGroups[match.dayHeader] = [];
                    }
                    dayGroups[match.dayHeader].push(match.card);
                });
                
                // Create day sections for results
                Object.keys(dayGroups).forEach(dayHeader => {
                    const daySection = document.createElement('div');
                    daySection.className = 'day-section';
                    daySection.style.marginBottom = '30px';
                    
                    const header = document.createElement('div');
                    header.className = 'day-header';
                    header.innerHTML = `<span>${dayHeader}</span><span class="day-count">${dayGroups[dayHeader].length} result${dayGroups[dayHeader].length !== 1 ? 's' : ''}</span>`;
                    daySection.appendChild(header);
                    
                    dayGroups[dayHeader].forEach(card => {
                        daySection.appendChild(card);
                    });
                    
                    resultsContent.appendChild(daySection);
                });
                
                // Show results container
                resultsContainer.classList.add('active');
                
                // Update results count
                resultsCount.textContent = `Found ${totalMatches} task${totalMatches !== 1 ? 's' : ''} across ${Object.keys(dayGroups).length} day${Object.keys(dayGroups).length !== 1 ? 's' : ''}`;
                
                // Scroll to results
                resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        
        // Set up search box event listener when page loads
        document.addEventListener('DOMContentLoaded', function() {
            const searchBox = document.getElementById('searchBox');
            if (searchBox) {
                searchBox.addEventListener('input', performSearch);
                
                // Add keyboard shortcut: Ctrl+K or Cmd+K to focus search
                document.addEventListener('keydown', function(e) {
                    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                        e.preventDefault();
                        searchBox.focus();
                    }
                    
                    // Escape to clear search
                    if (e.key === 'Escape' && document.activeElement === searchBox) {
                        searchBox.value = '';
                        performSearch();
                    }
                });
            }
            
            // Initialize timeline pagination
            initializeTimelinePagination();
        });

        function filterByDate() {
            const startDate = document.getElementById('dateFilterStart').value;
            const endDate = document.getElementById('dateFilterEnd').value || startDate;

            if (!startDate) return;

            const resultsContainer = document.getElementById('searchResultsContainer') || document.getElementById('statResultsContainer');
            const timelineWidget = document.querySelector('.timeline-widget');
            const timelineSection = document.querySelector('.timeline-section');

            // Use stat results container for date filter display
            const statContainer = document.getElementById('statResultsContainer');
            const statContent = document.getElementById('statResultsContent');
            const statTitle = document.getElementById('statResultsTitle');

            const startObj = new Date(startDate + 'T00:00:00');
            const endObj = new Date(endDate + 'T23:59:59');

            const startLabel = startObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
            const endLabel = endObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
            statTitle.textContent = startDate === endDate ? '📅 ' + startLabel : '📅 ' + startLabel + ' — ' + endLabel;

            statContent.innerHTML = '';
            let matchCount = 0;

            // Search upcoming tasks/events from DOM
            const daySections = document.querySelectorAll('.timeline-section .day-section');
            daySections.forEach(daySection => {
                if (!daySection.id || !daySection.id.startsWith('day-')) return;
                const dateStr = daySection.id.replace('day-', '');
                if (dateStr >= startDate && dateStr <= endDate) {
                    const tasks = daySection.querySelectorAll('.task-card');
                    if (tasks.length > 0) {
                        const dateObj = new Date(dateStr + 'T12:00:00');
                        const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
                        const header = document.createElement('div');
                        header.className = 'day-header';
                        header.innerHTML = '<span>' + dayName + '</span><span class="day-count">' + tasks.length + ' item' + (tasks.length !== 1 ? 's' : '') + '</span>';
                        statContent.appendChild(header);
                        tasks.forEach(card => {
                            statContent.appendChild(card.cloneNode(true));
                            matchCount++;
                        });
                    }
                }
            });

            // Search past events from JSON
            const pastEventsData = {past_events_json};
            let pastByDate = {};
            pastEventsData.forEach(evt => {
                if (evt.date >= startDate && evt.date <= endDate) {
                    if (!pastByDate[evt.date]) pastByDate[evt.date] = [];
                    pastByDate[evt.date].push(evt);
                }
            });

            Object.keys(pastByDate).sort().reverse().forEach(dateKey => {
                const events = pastByDate[dateKey];
                const dateObj = new Date(dateKey + 'T12:00:00');
                const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
                const header = document.createElement('div');
                header.className = 'day-header';
                header.innerHTML = '<span>📜 ' + dayName + '</span><span class="day-count">' + events.length + ' event' + (events.length !== 1 ? 's' : '') + '</span>';
                statContent.appendChild(header);

                events.forEach(evt => {
                    const card = document.createElement('div');
                    card.className = 'task-card priority-high meeting-completed';
                    let timeStr = evt.start_time ? '⏰ ' + evt.start_time + ' - ' + evt.end_time + ': ' : '';
                    let detailsHtml = '';
                    if (evt.details && evt.details.length > 0) {
                        detailsHtml = '<div class="meeting-details" style="margin-top:8px;">';
                        evt.details.forEach(d => {
                            if (d.includes('[') && d.includes('](')) {
                                const match = d.match(/\[(.+?)\]\((.+?)\)/);
                                if (match) {
                                    detailsHtml += '<div>' + d.replace(match[0], '<a href="' + match[2] + '" target="_blank">' + match[1] + '</a>') + '</div>';
                                } else { detailsHtml += '<div>' + d + '</div>'; }
                            } else { detailsHtml += '<div>' + d + '</div>'; }
                        });
                        detailsHtml += '</div>';
                    }
                    card.innerHTML = '<div class="task-title">' + timeStr + evt.title + '</div>' + detailsHtml +
                        '<div class="task-badges"><span class="task-badge">📅 Meeting</span><span class="task-badge completed-meeting">✅ COMPLETED</span></div>';
                    statContent.appendChild(card);
                    matchCount++;
                });
            });

            if (matchCount === 0) {
                statContent.innerHTML = '<div class="no-tasks">No tasks or events found for this date range</div>';
            }

            statContainer.classList.add('active');
            if (timelineWidget) timelineWidget.style.display = 'none';
            if (timelineSection) timelineSection.style.display = 'none';
            document.getElementById('dateFilterClear').style.display = '';
        }

        function clearDateFilter() {
            document.getElementById('dateFilterStart').value = '';
            document.getElementById('dateFilterEnd').value = '';
            document.getElementById('dateFilterClear').style.display = 'none';
            closeStatResults();
        }
        
        // Timeline pagination
        let currentWeekOffset = 0;
        let allTimelineDays = [];
        
        function initializeTimelinePagination() {
            const timelineTrack = document.getElementById('timelineTrack');
            if (!timelineTrack) return;
            
            // Collect all timeline days
            allTimelineDays = Array.from(timelineTrack.querySelectorAll('.timeline-day'));
            
            // Show first week
            updateTimelineView();
        }
        
        function changeWeek(direction) {
            currentWeekOffset += direction;
            updateTimelineView();
        }
        
        function updateTimelineView() {
            const daysPerWeek = 7;
            const startIdx = currentWeekOffset * daysPerWeek;
            const endIdx = startIdx + daysPerWeek;
            
            // Hide all days
            allTimelineDays.forEach(day => day.style.display = 'none');
            
            // Show only current week
            const visibleDays = allTimelineDays.slice(startIdx, endIdx);
            visibleDays.forEach(day => day.style.display = 'block');
            
            // Update navigation buttons
            const prevBtn = document.getElementById('prevWeekBtn');
            const nextBtn = document.getElementById('nextWeekBtn');
            const weekLabel = document.getElementById('weekLabel');
            const timelineTitle = document.getElementById('timelineTitle');
            
            if (prevBtn) {
                prevBtn.disabled = startIdx <= 0;
            }
            
            if (nextBtn) {
                nextBtn.disabled = endIdx >= allTimelineDays.length;
            }
            
            // Update week label and title with date range
            if (weekLabel && visibleDays.length > 0) {
                const firstDay = visibleDays[0].querySelector('.timeline-date')?.textContent || '';
                const lastDay = visibleDays[visibleDays.length - 1].querySelector('.timeline-date')?.textContent || '';
                
                if (currentWeekOffset === 0) {
                    weekLabel.textContent = 'This Week';
                } else if (currentWeekOffset === 1) {
                    weekLabel.textContent = 'Next Week';
                } else if (currentWeekOffset === -1) {
                    weekLabel.textContent = 'Last Week';
                } else if (currentWeekOffset > 1) {
                    weekLabel.textContent = `Week +${currentWeekOffset}`;
                } else {
                    weekLabel.textContent = `Week ${currentWeekOffset}`;
                }
                
                // Update timeline title with date range
                if (timelineTitle) {
                    timelineTitle.textContent = `🗓️ Timeline View (${firstDay} - ${lastDay})`;
                }
            }
        }
        
        // Completed tasks filter
        let showingThisWeekOnly = false;
        
        function toggleCompletedFilter(event) {
            if (event) event.stopPropagation();
            showingThisWeekOnly = !showingThisWeekOnly;
            const btn = document.getElementById('completedFilterBtn');
            const statNumber = document.querySelector('.stat-card.completed .stat-number');
            
            if (showingThisWeekOnly) {
                btn.classList.add('active');
                btn.textContent = 'Show All';
                statNumber.textContent = '{completed_this_week_count}';
            } else {
                btn.classList.remove('active');
                btn.textContent = 'This Week Only';
                statNumber.textContent = '{completed_count}';
            }
        }
        
        // Stat card filtering
        function showStatResults(filterType, event) {
            if (event) event.stopPropagation();
            
            const resultsContainer = document.getElementById('statResultsContainer');
            const resultsContent = document.getElementById('statResultsContent');
            const resultsTitle = document.getElementById('statResultsTitle');
            const timelineWidget = document.querySelector('.timeline-widget');
            
            // Close search results if open
            const searchResultsContainer = document.getElementById('searchResultsContainer');
            if (searchResultsContainer) {
                searchResultsContainer.classList.remove('active');
                document.getElementById('searchBox').value = '';
            }
            
            // Remove active class from all stat cards
            document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));
            
            // Special handling for completed tasks
            if (filterType === 'completed') {
                showCompletedTasks(resultsContainer, resultsContent, resultsTitle, timelineWidget, event);
                return;
            }

            // Special handling for past events
            if (filterType === 'past_events') {
                const allPastEvents = {past_events_json};
                let pastShowingAll = false;

                function renderPastEvents(showAll) {
                    const today = new Date();
                    const mondayOffset = today.getDay() === 0 ? 6 : today.getDay() - 1;
                    const weekStart = new Date(today);
                    weekStart.setDate(today.getDate() - mondayOffset);
                    const weekStartStr = weekStart.toISOString().split('T')[0];

                    const filtered = showAll ? allPastEvents : allPastEvents.filter(e => e.date >= weekStartStr);

                    resultsTitle.textContent = showAll ? '📜 All Past Events' : '📜 Past Events (This Week)';
                    resultsContent.innerHTML = '';

                    // Filter toggle button
                    const toggleDiv = document.createElement('div');
                    toggleDiv.style.cssText = 'text-align:center; margin-bottom:16px;';
                    const toggleBtn = document.createElement('button');
                    toggleBtn.className = 'stat-filter-button';
                    toggleBtn.textContent = showAll ? 'This Week Only' : 'Show All';
                    toggleBtn.style.cssText = 'padding:6px 16px; border-radius:6px; border:1px solid #D1D5DB; background:#F3F4F6; color:#6B7280; cursor:pointer; font-size:13px;';
                    toggleBtn.onclick = function(e) {
                        e.stopPropagation();
                        pastShowingAll = !pastShowingAll;
                        renderPastEvents(pastShowingAll);
                    };
                    toggleDiv.appendChild(toggleBtn);
                    resultsContent.appendChild(toggleDiv);

                    if (filtered.length === 0) {
                        resultsContent.innerHTML += '<div class="no-tasks">No past events found</div>';
                    } else {
                        let currentDate = '';
                        filtered.forEach(evt => {
                            if (evt.date !== currentDate) {
                                currentDate = evt.date;
                                const dateObj = new Date(evt.date + 'T12:00:00');
                                const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
                                const header = document.createElement('div');
                                header.className = 'day-header';
                                header.innerHTML = '<span>📜 ' + dayName + '</span>';
                                resultsContent.appendChild(header);
                            }
                            const card = document.createElement('div');
                            card.className = 'task-card priority-high meeting-completed';
                            let timeStr = evt.start_time ? '⏰ ' + evt.start_time + ' - ' + evt.end_time + ': ' : '';
                            let detailsHtml = '';
                            if (evt.details && evt.details.length > 0) {
                                detailsHtml = '<div class="meeting-details" style="margin-top:8px;">';
                                evt.details.forEach(d => {
                                    if (d.includes('[') && d.includes('](')) {
                                        const match = d.match(/\[(.+?)\]\((.+?)\)/);
                                        if (match) {
                                            detailsHtml += '<div>' + d.replace(match[0], '<a href="' + match[2] + '" target="_blank">' + match[1] + '</a>') + '</div>';
                                        } else {
                                            detailsHtml += '<div>' + d + '</div>';
                                        }
                                    } else {
                                        detailsHtml += '<div>' + d + '</div>';
                                    }
                                });
                                detailsHtml += '</div>';
                            }
                            card.innerHTML = '<div class="task-title">' + timeStr + evt.title + '</div>' + detailsHtml +
                                '<div class="task-badges"><span class="task-badge">📅 Meeting</span><span class="task-badge completed-meeting">✅ COMPLETED</span></div>';
                            resultsContent.appendChild(card);
                        });
                    }
                }

                renderPastEvents(false);
                resultsContainer.classList.add('active');
                if (timelineWidget) timelineWidget.style.display = 'none';
                document.querySelector('.timeline-section').style.display = 'none';
                return;
            }
            
            // Collect matching tasks from all day sections
            const allDaySections = document.querySelectorAll('.timeline-section .day-section');
            const matchingTasks = [];
            
            allDaySections.forEach(daySection => {
                const dayHeader = daySection.querySelector('.day-header span')?.textContent || '';
                const tasksInDay = daySection.querySelectorAll('.task-card');
                
                tasksInDay.forEach(card => {
                    let matches = false;
                    
                    if (filterType === 'overdue') {
                        // Check if task is in overdue section or has overdue badge
                        matches = dayHeader.includes('Overdue') || 
                                 card.classList.contains('priority-high') &&
                                 Array.from(card.querySelectorAll('.task-badge')).some(b => b.textContent.includes('OVERDUE'));
                    } else if (filterType === 'today') {
                        matches = dayHeader.includes('TODAY');
                    } else if (filterType === 'week') {
                        // Tasks through end of this week (Sunday)
                        if (daySection.id && daySection.id.startsWith('day-')) {
                            const dateStr = daySection.id.replace('day-', '');
                            const sectionDate = new Date(dateStr + 'T12:00:00');
                            const today = new Date();
                            const daysUntilSunday = 6 - today.getDay(); // Sunday=0 becomes 6, Mon=1 becomes 5, etc
                            const sunday = new Date(today);
                            sunday.setDate(today.getDate() + (daysUntilSunday === -1 ? 6 : daysUntilSunday));
                            sunday.setHours(23, 59, 59);
                            matches = sectionDate <= sunday && !dayHeader.includes('Overdue');
                        }
                    } else if (filterType === 'blocked') {
                        matches = card.classList.contains('blocked') ||
                                 Array.from(card.querySelectorAll('.task-badge')).some(b => b.textContent.includes('BLOCKED'));
                    }
                    
                    if (matches) {
                        matchingTasks.push({
                            card: card.cloneNode(true),
                            dayHeader: dayHeader
                        });
                    }
                });
            });
            
            // Set title based on filter type
            const titles = {
                'overdue': '🔴 Overdue Tasks',
                'today': '🟠 Tasks Due Today',
                'week': '🔵 Tasks Due This Week',
                'blocked': '🟣 Blocked Tasks',
                'completed': '🟢 Completed Tasks',
                'past_events': '📜 Past Events'
            };
            
            resultsTitle.textContent = titles[filterType] || 'Filtered Tasks';
            
            // Build results
            resultsContent.innerHTML = '';
            
            if (matchingTasks.length === 0) {
                resultsContent.innerHTML = '<div class="no-tasks">No tasks found in this category</div>';
            } else {
                // Group by day
                const dayGroups = {};
                matchingTasks.forEach(match => {
                    if (!dayGroups[match.dayHeader]) {
                        dayGroups[match.dayHeader] = [];
                    }
                    dayGroups[match.dayHeader].push(match.card);
                });
                
                // Create day sections
                Object.keys(dayGroups).forEach(dayHeader => {
                    const daySection = document.createElement('div');
                    daySection.className = 'day-section';
                    daySection.style.marginBottom = '30px';
                    
                    const header = document.createElement('div');
                    header.className = 'day-header';
                    header.innerHTML = `<span>${dayHeader}</span><span class="day-count">${dayGroups[dayHeader].length} task${dayGroups[dayHeader].length !== 1 ? 's' : ''}</span>`;
                    daySection.appendChild(header);
                    
                    dayGroups[dayHeader].forEach(card => {
                        daySection.appendChild(card);
                    });
                    
                    resultsContent.appendChild(daySection);
                });
            }
            
            // Hide timeline widget and show results
            if (timelineWidget) {
                timelineWidget.style.display = 'none';
            }
            resultsContainer.classList.add('active');
            
            // Highlight the clicked stat card
            event.currentTarget.classList.add('active');
            
            // Scroll to results
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        function closeStatResults() {
            const resultsContainer = document.getElementById('statResultsContainer');
            const timelineWidget = document.querySelector('.timeline-widget');
            
            // Hide results container
            resultsContainer.classList.remove('active');
            
            // Show timeline widget
            if (timelineWidget) {
                timelineWidget.style.display = '';
            }
            
            // Don't touch day-details-container - let CSS classes handle it
            
            // Remove active class from stat cards
            document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));
            
            // Scroll to timeline
            if (timelineWidget) {
                timelineWidget.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        
        // Show completed tasks
        function showCompletedTasks(resultsContainer, resultsContent, resultsTitle, timelineWidget, event) {
            // Hide timeline widget
            if (timelineWidget) {
                timelineWidget.style.display = 'none';
            }
            
            // Set title
            resultsTitle.textContent = '🟢 Completed Tasks';
            
            // Get completed tasks data (injected from Python)
            const completedTasksData = {completed_tasks_json};
            
            // Build results
            resultsContent.innerHTML = '';
            
            if (!completedTasksData || completedTasksData.length === 0) {
                resultsContent.innerHTML = '<div class="no-tasks">No completed tasks found</div>';
            } else {
                // Group by completion date
                const dateGroups = {};
                completedTasksData.forEach(task => {
                    const date = task.completed_date || 'Unknown Date';
                    if (!dateGroups[date]) {
                        dateGroups[date] = [];
                    }
                    dateGroups[date].push(task);
                });
                
                // Sort dates (most recent first)
                const sortedDates = Object.keys(dateGroups).sort((a, b) => {
                    if (a === 'Unknown Date') return 1;
                    if (b === 'Unknown Date') return -1;
                    return new Date(b) - new Date(a);
                });
                
                // Create sections for each date
                sortedDates.forEach(date => {
                    const tasks = dateGroups[date];
                    const daySection = document.createElement('div');
                    daySection.className = 'day-section';
                    daySection.style.marginBottom = '30px';
                    
                    const header = document.createElement('div');
                    header.className = 'day-header';
                    header.innerHTML = `<span>Completed: ${date}</span><span class="day-count">${tasks.length} task${tasks.length !== 1 ? 's' : ''}</span>`;
                    daySection.appendChild(header);
                    
                    // Add each task
                    tasks.forEach(task => {
                        const taskCard = document.createElement('div');
                        taskCard.className = 'task-card meeting-completed';

                        const taskTitle = document.createElement('div');
                        taskTitle.className = 'task-title';
                        taskTitle.textContent = '✅ ' + task.title;
                        taskCard.appendChild(taskTitle);
                        
                        const taskMeta = document.createElement('div');
                        taskMeta.className = 'task-meta';
                        
                        if (task.project) {
                            const projectBadge = document.createElement('span');
                            projectBadge.className = 'task-badge project';
                            projectBadge.textContent = task.project;
                            taskMeta.appendChild(projectBadge);
                        }
                        
                        if (task.type) {
                            const typeBadge = document.createElement('span');
                            typeBadge.className = 'task-badge';
                            typeBadge.textContent = task.type;
                            taskMeta.appendChild(typeBadge);
                        }

                        const completedBadge = document.createElement('span');
                        completedBadge.className = 'task-badge completed-meeting';
                        completedBadge.textContent = '✅ COMPLETED';
                        taskMeta.appendChild(completedBadge);

                        taskCard.appendChild(taskMeta);

                        // Task details (notes, contacts, action, links)
                        const detailItems = [];
                        if (task.contacts && task.contacts.length > 0) {
                            detailItems.push('👤 Contact: ' + task.contacts.join(', '));
                        }
                        if (task.notes) {
                            detailItems.push('📝 ' + task.notes);
                        }
                        if (task.action) {
                            detailItems.push('🎯 ' + task.action);
                        }
                        if (task.links) {
                            const linkLabels = {url: 'Link', action_plan: 'Action Plan', test_script: 'Test Script', email_reference: 'Email Reference', file: 'File'};
                            const linkIcons = {url: '🔗', action_plan: '📋', test_script: '🧪', email_reference: '📧', file: '📄'};
                            Object.keys(task.links).forEach(key => {
                                detailItems.push(linkIcons[key] + ' <a href="' + task.links[key] + '" target="_blank" style="color: #2563eb; text-decoration: underline;">' + linkLabels[key] + '</a>');
                            });
                        }
                        if (detailItems.length > 0) {
                            const detailsDiv = document.createElement('div');
                            detailsDiv.style.cssText = 'margin-top: 8px; padding-top: 8px; border-top: 1px solid #E5E7EB;';
                            detailItems.forEach(item => {
                                const line = document.createElement('div');
                                line.style.cssText = 'font-size: 13px; color: #6B7280; margin: 3px 0; padding-left: 8px;';
                                line.innerHTML = item;
                                detailsDiv.appendChild(line);
                            });
                            taskCard.appendChild(detailsDiv);
                        }

                        daySection.appendChild(taskCard);
                    });
                    
                    resultsContent.appendChild(daySection);
                });
            }
            
            // Show results container
            resultsContainer.classList.add('active');
            
            // Highlight the clicked stat card
            if (event && event.currentTarget) {
                event.currentTarget.classList.add('active');
            }
            
            // Scroll to results
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Task Deadline Dashboard</h1>
            <p class="subtitle">Updated at {generated_time}</p>
            <div class="search-container">
                <input type="text" id="searchBox" class="search-box" placeholder="🔍 Search tasks and events...">
                <span class="search-icon">🔍</span>
            </div>
            <div class="date-filter-bar">
                <label for="dateFilter">📅 Filter by date:</label>
                <input type="date" id="dateFilterStart" class="date-filter-input">
                <span class="date-filter-sep">to</span>
                <input type="date" id="dateFilterEnd" class="date-filter-input">
                <button id="dateFilterBtn" class="date-filter-btn" onclick="filterByDate()">Filter</button>
                <button id="dateFilterClear" class="date-filter-btn clear" onclick="clearDateFilter()" style="display:none;">Clear</button>
            </div>
            <div id="searchResultsCount" class="search-results-count"></div>
            
            <!-- Search Results Container -->
            <div id="searchResultsContainer" class="search-results-container">
                <div id="searchResultsContent"></div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card urgent" onclick="showStatResults('overdue')">
                <div class="stat-number">{overdue_count}</div>
                <div class="stat-label">Overdue</div>
            </div>
            <div class="stat-card today" onclick="showStatResults('today')">
                <div class="stat-number">{today_count}</div>
                <div class="stat-label">Due Today</div>
            </div>
            <div class="stat-card this-week" onclick="showStatResults('week')">
                <div class="stat-number">{this_week_count}</div>
                <div class="stat-label">Due This Week</div>
            </div>
            <div class="stat-card blocked" onclick="showStatResults('blocked')">
                <div class="stat-number">{blocked_count}</div>
                <div class="stat-label">Blocked Tasks</div>
            </div>
            <div class="stat-card completed" onclick="showStatResults('completed', event)">
                <div class="stat-number">{completed_count}</div>
                <div class="stat-label">Completed</div>
                <button class="stat-filter-button" id="completedFilterBtn" onclick="toggleCompletedFilter(event)">
                    This Week Only
                </button>
            </div>
        </div>
        
        <!-- Stat Results Container -->
        <div id="statResultsContainer" class="stat-results-container">
            <div class="stat-results-header">
                <h2 id="statResultsTitle" class="stat-results-title">Results</h2>
                <button class="close-stat-results" onclick="closeStatResults()">← Back to Timeline</button>
            </div>
            <div id="statResultsContent"></div>
        </div>
        
        <div class="timeline-widget">
            <div class="timeline-header">
                <h2 id="timelineTitle">🗓️ Timeline View</h2>
                <div class="timeline-nav">
                    <button class="timeline-nav-button" id="prevWeekBtn" onclick="changeWeek(-1)">← Prev</button>
                    <div class="timeline-week-label" id="weekLabel">This Week</div>
                    <button class="timeline-nav-button" id="nextWeekBtn" onclick="changeWeek(1)">Next →</button>
                </div>
            </div>
            <div class="timeline-scroll-container">
                <div class="timeline-track" id="timelineTrack">
                    {timeline_widget_html}
                </div>
            </div>
            <div class="scroll-hint">Click a date to see details</div>
        </div>
        
        <div id="day-details-container" class="day-details-container">
            <div class="day-details-header">
                <h2 id="day-details-title" class="day-details-title">Day Details</h2>
                <button class="close-details" onclick="closeDayDetails()">✕ Close</button>
            </div>
            <div id="day-details-content"></div>
        </div>
        
        <div class="timeline-section" style="display: none;">
            {timeline_html}
        </div>
    </div>
</body>
</html>
"""


class DeadlineVisualizer:
    def __init__(self, tasks_file, calendar_file=None):
        self.tasks_file = Path(tasks_file)
        self.calendar_file = Path(calendar_file) if calendar_file else None
        self.tasks = []
        self.calendar_events = []
        self.today = datetime.now().date()
        self.tasks_data = None  # Store full JSON data

    def count_completed_tasks(self):
        """Count completed tasks from tasks.json"""
        if not self.tasks_data:
            with open(self.tasks_file, "r") as f:
                self.tasks_data = json.load(f)

        # Filter completed tasks
        completed_tasks = [
            task
            for task in self.tasks_data.get("tasks", [])
            if task.get("status") == "completed"
        ]

        total_completed = len(completed_tasks)

        # Count completed this week
        week_ago = self.today - timedelta(days=7)
        completed_this_week = 0

        for task in completed_tasks:
            completed_date_str = task.get("completed_date")
            if completed_date_str:
                try:
                    # Parse "2026-04-07" format
                    completed_date = datetime.strptime(
                        completed_date_str, "%Y-%m-%d"
                    ).date()
                    if completed_date >= week_ago:
                        completed_this_week += 1
                except:
                    continue

        return total_completed, completed_this_week

    def get_completed_tasks_list(self):
        """Get list of completed tasks with details"""
        if not self.tasks_data:
            with open(self.tasks_file, "r") as f:
                self.tasks_data = json.load(f)

        # Filter completed tasks
        completed_tasks = [
            task
            for task in self.tasks_data.get("tasks", [])
            if task.get("status") == "completed"
        ]

        # Format for display (convert date format)
        formatted_tasks = []
        for task in completed_tasks:
            completed_date = task.get("completed_date", "Unknown")
            # Convert "2026-04-07" to "04/07/2026" format for consistency
            if completed_date and completed_date != "Unknown":
                try:
                    date_obj = datetime.strptime(completed_date, "%Y-%m-%d")
                    completed_date = date_obj.strftime("%m/%d/%Y")
                except:
                    pass

            # Build metadata links
            metadata = task.get("metadata", {})
            links = {}
            base_dir = str(Path(self.tasks_file).parent.parent)
            if metadata.get("url"):
                links["url"] = metadata["url"]
            if metadata.get("action_plan"):
                links["action_plan"] = "file://" + str(Path(base_dir) / metadata["action_plan"])
            if metadata.get("test_script"):
                links["test_script"] = "file://" + str(Path(base_dir) / metadata["test_script"])
            if metadata.get("email_reference"):
                links["email_reference"] = "file://" + str(Path(base_dir) / metadata["email_reference"])
            if metadata.get("file"):
                links["file"] = "file://" + str(Path(base_dir) / metadata["file"])

            formatted_tasks.append(
                {
                    "title": task.get("title", "Untitled"),
                    "completed_date": completed_date,
                    "project": task.get("project", "Unknown"),
                    "type": task.get("type", "Unknown"),
                    "notes": task.get("notes"),
                    "contacts": task.get("contacts", []),
                    "action": task.get("action"),
                    "links": links,
                }
            )

        return formatted_tasks

    def parse_tasks(self):
        """Parse tasks from tasks.json"""
        with open(self.tasks_file, "r") as f:
            self.tasks_data = json.load(f)

        # Process each task
        for task in self.tasks_data.get("tasks", []):
            # Skip completed tasks
            if task.get("status") == "completed":
                continue

            # Parse due_date from "2026-04-07" format
            due_date = None
            due_date_str = task.get("due_date")
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except:
                    pass

            # Get blocked status
            is_blocked = task.get("blocked", False)

            # Extract contacts - handle both string and list
            contacts = task.get("contacts", [])
            contact = None
            if contacts:
                if isinstance(contacts, list) and len(contacts) > 0:
                    contact = ", ".join(contacts)
                elif isinstance(contacts, str):
                    contact = contacts

            # Get subtasks metadata
            subtasks = task.get("subtasks", [])
            tech = None
            note = None
            estimated = None

            # Check subtasks for additional metadata
            for subtask in subtasks:
                if not tech and subtask.get("tech"):
                    tech = subtask.get("tech")
                if not note and subtask.get("note"):
                    note = subtask.get("note")
                if not estimated and subtask.get("estimated"):
                    estimated = subtask.get("estimated")

            # Also check main task for these fields
            if not tech:
                tech = task.get("tech")
            if not note:
                note = task.get("notes")
            if not estimated:
                estimated = task.get("estimated_hours")

            self.tasks.append(
                {
                    "title": task.get("title", "Untitled"),
                    "priority": task.get("priority", "medium"),
                    "due_date": due_date,
                    "is_blocked": is_blocked,
                    "project": task.get("project", "Unknown"),
                    "raw": task.get("description", ""),  # For filtering
                    "type": "task",
                    "task_type": task.get("type"),
                    "status": task.get("status"),
                    "contact": contact,
                    "note": note,
                    "estimated": estimated,
                    "tech": tech,
                    "action": task.get("action"),
                    "metadata": task.get("metadata", {}),
                }
            )

    def parse_calendar(self):
        """Parse calendar.json for meetings and time blocks"""
        if not self.calendar_file or not self.calendar_file.exists():
            return

        with open(self.calendar_file, "r") as f:
            calendar_data = json.load(f)

        # Process each event
        for event in calendar_data.get("events", []):
            # Parse date from "2026-04-07" format
            event_date = None
            date_str = event.get("date")
            if date_str:
                try:
                    event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except:
                    continue

            if not event_date:
                continue

            # Get event type
            event_type = event.get("type", "meeting")
            is_personal = event.get("is_personal", False)

            # Build details list
            details = []

            # Add zoom link
            zoom_link = event.get("zoom_link")
            if zoom_link:
                details.append(f"🔗 [Join Meeting]({zoom_link})")

            # Add location
            location = event.get("location")
            if location:
                details.append(f"📍 Location: {location}")

            # Add meeting ID
            meeting_id = event.get("meeting_id")
            if meeting_id:
                details.append(f"🆔 Meeting ID: {meeting_id}")

            # Add dial-in
            dial_in = event.get("dial_in")
            if dial_in:
                details.append(f"📞 Dial-in: {dial_in}")

            # Add agenda link
            agenda_link = event.get("agenda_link")
            if agenda_link:
                details.append(f"📄 [Meeting Agenda]({agenda_link})")

            # Add notes
            notes = event.get("notes")
            if notes:
                details.append(f"📝 {notes}")

            # Add recurring indicator
            if event.get("recurring"):
                details.append("🔁 Recurring")

            # Check if meeting has ended
            is_meeting_completed = False
            end_time_str = event.get("end_time")
            if end_time_str and event_date == self.today:
                try:
                    end_dt = datetime.strptime(f"{event_date} {end_time_str}", "%Y-%m-%d %I:%M %p")
                    if datetime.now() > end_dt:
                        is_meeting_completed = True
                except:
                    pass
            elif event_date < self.today:
                is_meeting_completed = True

            # Create event object
            if event_type in ["meeting", "personal"]:
                meeting_event = {
                    "title": event.get("title", "Untitled Event"),
                    "date": event_date,
                    "start_time": event.get("start_time"),
                    "end_time": event.get("end_time"),
                    "type": "meeting",
                    "priority": "high",
                    "is_personal": is_personal,
                    "is_meeting_completed": is_meeting_completed,
                    "details": details,
                }
                self.calendar_events.append(meeting_event)

    def get_all_items(self):
        """Combine tasks and calendar events into one list"""
        all_items = []

        # Add tasks - preserve all metadata fields
        for task in self.tasks:
            all_items.append(task)

        # Add calendar events - ONLY meetings, not time blocks
        for event in self.calendar_events:
            if event["type"] == "meeting":  # Only include meetings
                is_personal = event.get("is_personal", False)
                all_items.append(
                    {
                        "title": event["title"],
                        "priority": "high",
                        "due_date": event["date"],
                        "is_blocked": False,
                        "project": "🏠 Personal" if is_personal else "📅 Meeting",
                        "type": event["type"],
                        "is_personal": is_personal,
                        "is_meeting_completed": event.get("is_meeting_completed", False),
                        "start_time": event.get("start_time"),
                        "end_time": event.get("end_time"),
                        "details": event.get("details", []),  # Include meeting details
                        # No task-specific metadata for meetings
                        "task_type": None,
                        "status": None,
                        "contact": None,
                        "note": None,
                        "estimated": None,
                        "tech": None,
                        "action": None,
                    }
                )

        return all_items

    def extract_due_date(self, text):
        """Extract due date from task text"""
        # Pattern: [Due: MM/DD/YYYY (Day)] or [Due: MM/DD/YYYY]
        pattern = r"\[Due: (\d{2}/\d{2}/\d{4})"
        match = re.search(pattern, text)
        if match:
            try:
                date_str = match.group(1)
                return datetime.strptime(date_str, "%m/%d/%Y").date()
            except Exception as e:
                print(f"Warning: Could not parse date '{date_str}': {e}")
                pass

        # Pattern: [Due: Tomorrow]
        if "[Due: Tomorrow]" in text or "[Due: tomorrow]" in text:
            return (datetime.now() + timedelta(days=1)).date()

        # Pattern: [Due: TBD] or [Due: Next week]
        if "[Due: TBD]" in text or "[Due: Next week]" in text:
            return None

        return None

        return None

    def extract_project(self, text):
        """Extract project name from task text"""
        pattern = r"\[Project: ([^\]]+)\]"
        match = re.search(pattern, text)
        return match.group(1) if match else "Unknown"

    def extract_metadata(self, text, field_name):
        """Extract metadata field from task text"""
        pattern = rf"\[{field_name}: ([^\]]+)\]"
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def categorize_tasks(self):
        """Categorize tasks by deadline urgency"""
        categorized = defaultdict(list)

        # Get combined list of tasks and calendar events
        all_items = self.get_all_items()

        for task in all_items:
            if not task["due_date"]:
                categorized["no_deadline"].append(task)
                continue

            days_until = (task["due_date"] - self.today).days

            # Collect past calendar events separately (past days + today's completed meetings)
            if task.get("type") == "meeting" and days_until < 0:
                categorized["past_events"].append(task)
                continue
            if task.get("type") == "meeting" and days_until == 0 and task.get("is_meeting_completed"):
                categorized["past_events"].append(task)
                # Also keep in today so it shows on the today view with completed badge
                categorized["today"].append(task)
                continue

            if days_until < 0:
                categorized["overdue"].append(task)
            elif days_until == 0:
                categorized["today"].append(task)
            elif days_until <= 149:
                categorized[f"day_{days_until}"].append(task)
            else:
                categorized["later"].append(task)

        return categorized

    def generate_timeline_widget_html(self, categorized):
        """Generate the interactive timeline widget"""
        html = []

        # Get all dates with items (next 14 days)
        date_items = defaultdict(lambda: {"meetings": 0, "tasks": 0, "all": []})

        all_items = self.get_all_items()

        for item in all_items:
            if item.get("due_date"):
                date = item["due_date"]
                date_items[date]["all"].append(item)

                if item.get("type") == "meeting":
                    date_items[date]["meetings"] += 1
                else:
                    date_items[date]["tasks"] += 1

        # Generate timeline days for next 5 months (150 days)
        for i in range(150):
            date = self.today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            day_name = date.strftime("%a")
            date_display = date.strftime("%b %d")

            is_today = date == self.today
            today_class = "today" if is_today else ""

            # Create readable day label
            day_label = date.strftime("%A, %B %d")
            if is_today:
                day_label = f"📍 TODAY - {day_label}"
            elif i == 1:
                day_label = f"Tomorrow - {day_label}"

            items = date_items[date]
            total_items = items["meetings"] + items["tasks"]

            html.append(
                f'<div class="timeline-day {today_class}" data-date="day-{date_str}" onclick="scrollToDay(\'day-{date_str}\', \'{day_label}\')">'
            )
            html.append(f'<div class="timeline-date">{date_display}</div>')
            html.append(f'<div class="timeline-weekday">{day_name}</div>')

            if total_items > 0:
                html.append('<div class="timeline-indicators">')
                if items["meetings"] > 0:
                    html.append(
                        f'<span class="timeline-count meetings">📅 {items["meetings"]} meeting{"s" if items["meetings"] != 1 else ""}</span>'
                    )
                if items["tasks"] > 0:
                    html.append(
                        f'<span class="timeline-count tasks">📋 {items["tasks"]} task{"s" if items["tasks"] != 1 else ""}</span>'
                    )
                html.append("</div>")
            else:
                html.append('<div class="timeline-empty">Free</div>')

            html.append("</div>")

        return "\n".join(html)

    def generate_html(self):
        """Generate HTML dashboard"""
        categorized = self.categorize_tasks()

        # Calculate stats
        overdue_count = len(categorized["overdue"])
        today_count = len(categorized["today"])

        # Calculate days until end of this week (Sunday)
        days_until_sunday = 6 - self.today.weekday()  # Monday=0, Sunday=6
        if days_until_sunday == 0:
            days_until_sunday = 7  # If today is Sunday, show next week
        this_week_count = sum(
            len(tasks)
            for key, tasks in categorized.items()
            if key.startswith("day_") and int(key.split("_")[1]) <= days_until_sunday
        )

        blocked_count = sum(1 for task in self.tasks if task["is_blocked"])

        # Count completed tasks
        completed_count, completed_this_week_count = self.count_completed_tasks()

        # Count past events
        past_events_count = len(categorized.get("past_events", []))

        # Generate timeline widget
        timeline_widget_html = self.generate_timeline_widget_html(categorized)

        # Generate list view HTML
        timeline_html = self.generate_timeline_html(categorized)

        # Get completed tasks for stat card display
        completed_tasks_list = self.get_completed_tasks_list()

        # Fill template using replace instead of format to avoid CSS brace issues
        html = HTML_TEMPLATE
        html = html.replace(
            "{generated_time}", datetime.now().strftime("%I:%M %p on %B %d, %Y")
        )
        html = html.replace("{overdue_count}", str(overdue_count))
        html = html.replace("{today_count}", str(today_count))
        html = html.replace("{this_week_count}", str(this_week_count))
        html = html.replace("{blocked_count}", str(blocked_count))
        html = html.replace("{completed_count}", str(completed_count))
        html = html.replace(
            "{completed_this_week_count}", str(completed_this_week_count)
        )
        html = html.replace("{timeline_widget_html}", timeline_widget_html)
        html = html.replace("{timeline_html}", timeline_html)
        html = html.replace("{completed_tasks_json}", json.dumps(completed_tasks_list))
        html = html.replace("{past_events_count}", str(past_events_count))

        # Build past events JSON for stat card display
        past_events_list = []
        for event in categorized.get("past_events", []):
            past_events_list.append({
                "title": event["title"],
                "date": event["due_date"].strftime("%Y-%m-%d"),
                "start_time": event.get("start_time", ""),
                "end_time": event.get("end_time", ""),
                "project": event.get("project", ""),
                "details": event.get("details", []),
            })
        past_events_list.sort(key=lambda x: x["date"], reverse=True)
        html = html.replace("{past_events_json}", json.dumps(past_events_list))

        return html

    def generate_timeline_html(self, categorized):
        """Generate timeline section HTML"""
        html = []

        # Overdue tasks
        if categorized["overdue"]:
            html.append(
                self.render_day_section(
                    "🚨 OVERDUE", categorized["overdue"], "urgent", "overdue-section"
                )
            )

        # Today
        if categorized["today"]:
            date_id = f"day-{self.today.strftime('%Y-%m-%d')}"
            html.append(
                self.render_day_section(
                    "📍 TODAY", categorized["today"], "today", date_id
                )
            )

        # Next 150 days (5 months - to match timeline widget)
        # Generate sections for all days, even if empty, so timeline clicks work
        for i in range(1, 150):
            date = self.today + timedelta(days=i)
            day_name = date.strftime("%A, %B %d")
            if i == 1:
                day_name = f"Tomorrow - {day_name}"
            date_id = f"day-{date.strftime('%Y-%m-%d')}"

            key = f"day_{i}"
            tasks_for_day = categorized[key] if categorized[key] else []

            # Only render if there are tasks/events for this day
            if tasks_for_day:
                html.append(
                    self.render_day_section(
                        day_name, tasks_for_day, "upcoming", date_id
                    )
                )
            else:
                # Create empty placeholder section so the ID exists for timeline clicks
                html.append(
                    f'<div class="day-section" id="{date_id}" style="display:none;"></div>'
                )

        # Blocked tasks
        blocked_tasks = [t for t in self.tasks if t["is_blocked"] and not t["due_date"]]
        if blocked_tasks:
            html.append(
                self.render_day_section(
                    "⏸️ BLOCKED (No Deadline)", blocked_tasks, "blocked", None
                )
            )

        # No deadline tasks
        if categorized["no_deadline"]:
            no_deadline_not_blocked = [
                t for t in categorized["no_deadline"] if not t["is_blocked"]
            ]
            if no_deadline_not_blocked:
                html.append(
                    self.render_day_section(
                        "📋 No Deadline Set",
                        no_deadline_not_blocked[:5],
                        "no-deadline",
                        None,
                    )
                )

        # Past events (meetings that already happened)
        if categorized["past_events"]:
            past_count = len(categorized["past_events"])
            html.append(f'<div class="past-events-toggle">')
            html.append(f'<button onclick="var el=document.getElementById(\'past-events-container\'); el.style.display = el.style.display===\'none\' ? \'block\' : \'none\'; this.textContent = el.style.display===\'none\' ? \'Show Past Events ({past_count})\' : \'Hide Past Events\';">Show Past Events ({past_count})</button>')
            html.append('</div>')
            html.append('<div id="past-events-container" class="past-events-section" style="display:none;">')
            # Sort by date descending (most recent first)
            past_sorted = sorted(categorized["past_events"], key=lambda t: t["due_date"], reverse=True)
            # Group by date
            from itertools import groupby
            for date_key, group in groupby(past_sorted, key=lambda t: t["due_date"]):
                day_name = date_key.strftime("%A, %B %d")
                date_id = f"past-{date_key.strftime('%Y-%m-%d')}"
                html.append(
                    self.render_day_section(
                        f"📜 {day_name}", list(group), "past", date_id
                    )
                )
            html.append('</div>')

        if not html:
            html.append(
                '<div class="no-tasks">🎉 No urgent tasks! You\'re all caught up.</div>'
            )

        return "\n".join(html)

    def render_day_section(self, day_label, tasks, section_type, date_id=None):
        """Render a day section with tasks"""
        id_attr = f' id="{date_id}"' if date_id else ""
        html = [f'<div class="day-section"{id_attr}>']
        html.append(f'<div class="day-header">')
        html.append(f"<span>{day_label}</span>")
        html.append(
            f'<span class="day-count">{len(tasks)} task{"s" if len(tasks) != 1 else ""}</span>'
        )
        html.append("</div>")

        for task in tasks:
            priority_class = f"priority-{task['priority']}"
            blocked_class = "blocked" if task["is_blocked"] else ""
            personal_class = (
                "personal-meeting" if task.get("is_personal", False) else ""
            )
            completed_meeting_class = "meeting-completed" if task.get("is_meeting_completed") else ""

            html.append(
                f'<div class="task-card {priority_class} {blocked_class} {personal_class} {completed_meeting_class}">'
            )

            # Add icon and time based on type
            title_display = task["title"]
            if task.get("start_time"):
                # Meeting with time
                title_display = (
                    f"⏰ {task['start_time']} - {task['end_time']}: {title_display}"
                )
            else:
                # Regular task - add task emoji
                title_display = f"📋 {title_display}"

            escaped_title = title_display.replace("'", "\\'").replace('"', '&quot;')
            html.append(f'<div class="task-title">{title_display}<button class="copy-task-btn" onclick="navigator.clipboard.writeText(\'{escaped_title}\'); this.textContent=\'Copied!\'; setTimeout(()=>this.textContent=\'Copy\', 1200);" title="Copy task title">Copy</button></div>')

            # Add meeting details if available
            if task.get("details") and len(task["details"]) > 0:
                html.append('<div class="meeting-details">')
                for detail in task["details"]:
                    # Parse different types of details
                    detail_html = detail

                    # Make links clickable
                    if "[Join Meeting]" in detail:
                        # Extract URL from markdown link
                        link_match = re.search(r"\[Join Meeting\]\(([^)]+)\)", detail)
                        if link_match:
                            url = link_match.group(1)
                            detail_html = f'🔗 <a href="{url}" target="_blank" style="color: #2563eb; text-decoration: underline;">Join Meeting</a>'
                    elif "[Meeting Documents]" in detail:
                        link_match = re.search(
                            r"\[Meeting Documents\]\(([^)]+)\)", detail
                        )
                        if link_match:
                            url = link_match.group(1)
                            detail_html = f'📄 <a href="{url}" target="_blank" style="color: #2563eb; text-decoration: underline;">Meeting Documents</a>'
                    elif "[Meeting Agenda]" in detail:
                        link_match = re.search(r"\[Meeting Agenda\]\(([^)]+)\)", detail)
                        if link_match:
                            url = link_match.group(1)
                            detail_html = f'📄 <a href="{url}" target="_blank" style="color: #2563eb; text-decoration: underline;">Meeting Agenda</a>'

                    html.append(
                        f'<div style="font-size: 13px; color: #6B7280; margin: 3px 0; padding-left: 8px;">{detail_html}</div>'
                    )
                html.append("</div>")

            # Add task details if available (similar to meeting details)
            task_details = []
            if task.get("contact"):
                task_details.append(f"👤 Contact: {task['contact']}")
            if task.get("tech"):
                task_details.append(f"💻 Tech: {task['tech']}")
            if task.get("estimated"):
                task_details.append(f"⏱️ Estimated: {task['estimated']}")
            if task.get("note"):
                task_details.append(f"📝 {task['note']}")
            if task.get("action"):
                task_details.append(f"🎯 Action: {task['action']}")

            # Add metadata URLs and files
            metadata = task.get("metadata", {})
            if metadata:
                if metadata.get("tracker_url"):
                    url = metadata["tracker_url"]
                    task_details.append(
                        f'🔗 <a href="{url}" target="_blank" style="color: #2563eb; text-decoration: underline;">Website Updates Tracker</a>'
                    )
                if metadata.get("url"):
                    url = metadata["url"]
                    task_details.append(
                        f'🔗 <a href="{url}" target="_blank" style="color: #2563eb; text-decoration: underline;">Related Link</a>'
                    )
                if metadata.get("action_plan"):
                    file_path = metadata["action_plan"]
                    # Get base directory (parent of data/ folder)
                    base_dir = Path(self.tasks_file).parent.parent
                    full_path = base_dir / file_path
                    task_details.append(
                        f'📋 <a href="file://{full_path}" target="_blank" style="color: #2563eb; text-decoration: underline;">Action Plan</a>'
                    )
                if metadata.get("test_script"):
                    file_path = metadata["test_script"]
                    base_dir = Path(self.tasks_file).parent.parent
                    full_path = base_dir / file_path
                    task_details.append(
                        f'🧪 <a href="file://{full_path}" target="_blank" style="color: #2563eb; text-decoration: underline;">Test Script</a>'
                    )
                if metadata.get("file"):
                    task_details.append(f"📄 File: {metadata['file']}")

            if task_details:
                html.append(
                    '<div class="task-details" style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #E5E7EB;">'
                )
                for detail in task_details:
                    html.append(
                        f'<div style="font-size: 13px; color: #6B7280; margin: 3px 0; padding-left: 8px;">{detail}</div>'
                    )
                html.append("</div>")

            html.append('<div class="task-meta">')
            html.append(f'<span class="task-badge project">{task["project"]}</span>')
            html.append(
                f'<span class="task-badge">{task["priority"].upper()} priority</span>'
            )
            if task["is_blocked"]:
                html.append('<span class="task-badge blocked">⚠️ BLOCKED</span>')
            # Add OVERDUE badge for tasks in the overdue section
            if section_type == "urgent":
                html.append('<span class="task-badge urgent">🔴 OVERDUE</span>')
            # Add COMPLETED badge for meetings that have ended
            if task.get("is_meeting_completed"):
                html.append('<span class="task-badge completed-meeting">✅ COMPLETED</span>')
            html.append("</div>")
            html.append("</div>")

        html.append("</div>")
        return "\n".join(html)

    def save_html(self, output_file):
        """Save HTML to file"""
        html = self.generate_html()
        with open(output_file, "w") as f:
            f.write(html)
        print(f"✅ Dashboard generated: {output_file}")
        print(f"📊 Open in browser: file://{output_file.absolute()}")


def main():
    import sys

    base_dir = get_base_dir()  # Get from .env or auto-detect
    tasks_file = base_dir / "data" / "tasks.json"
    calendar_file = base_dir / "data" / "calendar.json"
    output_file = base_dir / "deadline_dashboard.html"

    # Check for filter argument
    filter_mode = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ["work", "work-only", "--work"]:
            filter_mode = "work"
        elif sys.argv[1] in ["all", "personal", "--all"]:
            filter_mode = "all"

    if not tasks_file.exists():
        print(f"❌ Error: {tasks_file} not found")
        return

    visualizer = DeadlineVisualizer(tasks_file, calendar_file)
    visualizer.parse_tasks()
    visualizer.parse_calendar()

    # Apply filter if specified
    if filter_mode == "work":
        print("🏢 Filtering to work-only content...")
        # Filter tasks
        visualizer.tasks = [t for t in visualizer.tasks if not is_personal_task(t)]
        # Filter calendar events
        visualizer.calendar_events = [
            e for e in visualizer.calendar_events if not is_personal_event(e)
        ]

    visualizer.save_html(output_file)

    print(f"\n📈 Stats:")
    print(f"   Total active tasks: {len(visualizer.tasks)}")
    print(
        f"   Tasks with deadlines: {sum(1 for t in visualizer.tasks if t['due_date'])}"
    )
    print(f"   Blocked tasks: {sum(1 for t in visualizer.tasks if t['is_blocked'])}")
    print(f"   Calendar events: {len(visualizer.calendar_events)}")
    if filter_mode == "work":
        print(f"   Filter: Work-only (personal items hidden)")


def is_personal_task(task):
    """Check if a task is marked as personal"""
    raw_text = task.get("raw", "")
    # Check for [Personal] tag or [Type: Personal]
    if "[Personal]" in raw_text or "[Type: Personal]" in raw_text:
        return True
    # Check project field
    project = task.get("project", "").lower()
    if "personal" in project:
        return True
    return False


def is_personal_event(event):
    """Check if a calendar event is marked as personal"""
    # Check if event was marked as personal during parsing
    if event.get("is_personal", False):
        return True

    # Check title for personal keywords (backup check)
    title = event.get("title", "")
    title_lower = title.lower()
    personal_keywords = [
        "personal",
        "birthday",
        "anniversary",
        "vacation",
        "doctor",
        "dentist",
        "[personal]",
    ]
    if any(keyword in title_lower for keyword in personal_keywords):
        return True

    # Check event details for personal markers
    details = event.get("details", [])
    for detail in details:
        if "[Personal]" in detail or "🏠" in detail:
            return True

    return False


if __name__ == "__main__":
    main()
