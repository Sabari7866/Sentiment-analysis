document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const tweetInput = document.getElementById('tweetInput');
    const loader = document.getElementById('loader');

    // UI Elements
    const fakeStatus = document.getElementById('fakeStatus');
    const fakeProgress = document.getElementById('fakeProgress');
    const summaryText = document.getElementById('summaryText');
    const vulnLevel = document.getElementById('vulnLevel');
    const emotionIcon = document.getElementById('emotionIcon');
    const emotionLabel = document.getElementById('emotionLabel');
    const posFeed = document.getElementById('posFeed');
    const negFeed = document.getElementById('negFeed');
    const recContent = document.getElementById('recommendationContent');
    const reviewModal = document.getElementById('reviewModal');
    const closeModal = document.getElementById('closeModal');
    const companyList = document.getElementById('companyList');
    
    // Modal Elements
    const modalCompany = document.getElementById('modalCompany');
    const modalReview = document.getElementById('modalReview');
    const modalLogo = document.getElementById('modalLogo');
    const modalSentiment = document.getElementById('modalSentiment');

    const fetchBtn = document.getElementById('fetchBtn');
    const liveKeyword = document.getElementById('liveKeyword');
    const manualInput = document.getElementById('manualInput');
    const liveInput = document.getElementById('liveInput');

    const API_URL = 'http://127.0.0.1:8888/predict';
    const FETCH_URL = 'http://127.0.0.1:8888/fetch_live';
    const DATASET_URL = 'http://127.0.0.1:8888/dataset';

    // 📂 Load Dataset Samples on Start
    async function loadDatasetSamples() {
        try {
            const response = await fetch(DATASET_URL);
            const data = await response.json();
            
            posFeed.innerHTML = data.positive.map(item => `<div class="feed-item historical">${item.tweet}</div>`).join('');
            negFeed.innerHTML = data.negative.map(item => `<div class="feed-item historical">${item.tweet}</div>`).join('');
        } catch (error) {
            console.error('Failed to load dataset samples:', error);
        }
    }

    loadDatasetSamples();

    // 📊 Initialize Three Mini Charts
    const createMiniChart = (id, color) => {
        return new Chart(document.getElementById(id).getContext('2d'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: [color, 'rgba(255,255,255,0.05)'],
                    borderWidth: 0
                }]
            },
            options: {
                cutout: '80%',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    };

    const posChart = createMiniChart('posChart', '#10b981');
    const neuChart = createMiniChart('neuChart', '#94a3b8');
    const negChart = createMiniChart('negChart', '#ef4444');

    // Expose charts globally so the stream engine (outside DOMContentLoaded) can update them
    window._posChart = posChart;
    window._neuChart = neuChart;
    window._negChart = negChart;

    analyzeBtn.addEventListener('click', async () => {
        const text = tweetInput.value.trim();
        if (!text) {
            alert('Please enter text for analysis!');
            return;
        }
        await performAnalysis(text);
    });

    fetchBtn.addEventListener('click', async () => {
        const keyword = liveKeyword.value.trim();
        if (!keyword) {
            alert('Please enter a keyword for live fetching!');
            return;
        }

        loader.classList.remove('hidden');
        try {
            const response = await fetch(FETCH_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword })
            });

            if (!response.ok) throw new Error('Fetch failed');
            const data = await response.json();
            
            if (data.tweets && data.tweets.length > 0) {
                // Analyze the first one for the main dashboard
                const firstTweet = data.tweets[0];
                await performAnalysis(firstTweet.text);
                
                // Add all to feed
                data.tweets.forEach(t => {
                    const newItem = `<div class="feed-item new-entry live-entry">
                        <span class="user">@${t.user}</span>
                        "${t.text.substring(0, 60)}..."
                        <span class="tag ${t.sentiment.toLowerCase()}">${t.sentiment}</span>
                    </div>`;
                    if (t.sentiment === 'Positive') posFeed.insertAdjacentHTML('afterbegin', newItem);
                    else negFeed.insertAdjacentHTML('afterbegin', newItem);
                });
            }
        } catch (error) {
            console.error('Fetch Error:', error);
            alert('Live Fetcher Error. Ensure app.py is running and keys are configured.');
        } finally {
            loader.classList.add('hidden');
        }
    });

    async function performAnalysis(text) {
        loader.classList.remove('hidden');
        try {
            await new Promise(r => setTimeout(r, 800));
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            if (!response.ok) throw new Error('API request failed');
            const data = await response.json();
            updateDashboard(data);
        } catch (error) {
            console.error('Error:', error);
            alert('MoodPulse API Error.');
        } finally {
            loader.classList.add('hidden');
        }
    }

    function updateDashboard(data) {
        // 1. Update Triple Charts
        posChart.data.datasets[0].data = [data.probs.pos, 100 - data.probs.pos];
        neuChart.data.datasets[0].data = [data.probs.neu, 100 - data.probs.neu];
        negChart.data.datasets[0].data = [data.probs.neg, 100 - data.probs.neg];

        posChart.update();
        neuChart.update();
        negChart.update();

        // 2. Fake Detection
        fakeStatus.innerText = data.fake.status;
        fakeStatus.style.color = (data.fake.status === "PLAGIARIZED" || data.fake.status === "SUSPICIOUS") ? "#ef4444" : "#3b82f6";
        fakeProgress.style.width = data.fake.prob + "%";

        // 3. Insights & Intel
        summaryText.innerText = data.summary;
        
        // Handle Product Intelligence
        const intelPanel = document.getElementById('productIntel');
        if (data.product_intel) {
            intelPanel.classList.remove('hidden');
            document.getElementById('productIssue').innerText = `Detected weakness in ${data.product_intel.target}.`;
            document.getElementById('altProduct').innerText = data.product_intel.alternative;
            document.getElementById('altReason').innerText = data.product_intel.suggestion;
        } else {
            intelPanel.classList.add('hidden');
        }

        // 4. Emotion Display
        emotionIcon.innerText = data.emotion.icon;
        emotionLabel.innerText = data.emotion.label;

        // Populate Hashtags into Company Intel
        if (data.hashtags && data.hashtags.length > 0) {
            companyList.innerHTML = data.hashtags.map(h => `<span class="pill">#${h}</span>`).join('');
        }

        // 5. Feed Boxes (Prepend new results)
        const { company, review } = parseCompanyReview(data.original_text);
        
        const brandHtml = company ? `<span class="company-link" onclick="openReviewModal('${company}', '${review.replace(/'/g, "\\'")}', '${data.probs.pos >= data.probs.neg ? 'Positive' : 'Negative'}')">${company}</span>` : '';
        const feedText = `"${review.length > 50 ? review.substring(0, 47) + '...' : review}"`;
        const newItem = `<div class="feed-item new-entry">${brandHtml}${feedText}</div>`;
        
        if (data.probs.pos >= data.probs.neg) {
            posFeed.insertAdjacentHTML('afterbegin', newItem);
            if (posFeed.children.length > 6) posFeed.lastElementChild.remove();
        } else {
            negFeed.insertAdjacentHTML('afterbegin', newItem);
            if (negFeed.children.length > 6) negFeed.lastElementChild.remove();
        }

        if (company) updateCompanyPills(company);

        // 6. Recommendation
        const rec = data.recommendation;
        const recTitle = typeof rec === 'object' ? (rec.title || '') : rec;
        const recType  = typeof rec === 'object' ? (rec.type  || '') : '';
        const recUrl   = typeof rec === 'object' ? (rec.url   || '#') : '#';
        const recDesc  = typeof rec === 'object' && rec.description ? rec.description : (data.description || '');

        recContent.innerHTML =
            '<div class="rec-tag">' + (data.mood || 'Detected Topic') + '</div>' +
            (recType ? '<span style="font-size:0.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;">' + recType + '</span><br>' : '') +
            '<h4 style="margin:4px 0 6px;">' + recTitle + '</h4>' +
            '<p>' + recDesc + '</p>' +
            '<a href="' + recUrl + '" target="_blank" class="rec-link">Launch Content →</a>';

    }

    // 🔍 Utility: Parse Company and Review
    function parseCompanyReview(text) {
        const companyMatch = text.match(/Company:\s*([^,\n]+)/i);
        const reviewMatch = text.match(/Review:\s*(.+)/is);
        
        return {
            company: companyMatch ? companyMatch[1].trim() : null,
            review: reviewMatch ? reviewMatch[1].trim() : text
        };
    }

    // 💊 Company Tracking
    const trackedCompanies = new Set();
    function updateCompanyPills(name) {
        if (trackedCompanies.has(name)) return;
        trackedCompanies.add(name);
        
        const pill = document.createElement('div');
        pill.className = 'brand-pill';
        pill.innerText = name;
        companyList.appendChild(pill);
    }

    // 🎭 Modal Logic
    window.openReviewModal = (company, review, sentiment) => {
        modalCompany.innerText = company;
        modalReview.innerText = review;
        modalLogo.innerText = company.charAt(0).toUpperCase();
        modalSentiment.innerText = sentiment;
        modalSentiment.className = `sentiment-tag ${sentiment === 'Positive' ? 'pos' : 'neg'}`;
        
        reviewModal.classList.remove('hidden');
    };

    closeModal.addEventListener('click', () => reviewModal.classList.add('hidden'));
    window.addEventListener('click', (e) => {
        if (e.target === reviewModal) reviewModal.classList.add('hidden');
    });

    window.switchInputMode = function(mode) {
        const tabs = document.querySelectorAll('.input-tab');
        tabs.forEach(t => t.classList.remove('active'));

        if (mode === 'manual') {
            document.querySelector('.input-tab[onclick*="manual"]').classList.add('active');
            manualInput.classList.remove('hidden');
            liveInput.classList.add('hidden');
        } else {
            document.querySelector('.input-tab[onclick*="live"]').classList.add('active');
            manualInput.classList.add('hidden');
            liveInput.classList.remove('hidden');
        }
    };

    window.switchFeed = function(type) {
        const posFeed = document.getElementById('posFeed');
        const negFeed = document.getElementById('negFeed');
        const tabs = document.querySelectorAll('.tab-btn');

        tabs.forEach(t => {
            if (t.dataset.tab === type) t.classList.add('active');
            else t.classList.remove('active');
        });

        if (type === 'pos') {
            posFeed.classList.add('active');
            posFeed.classList.remove('hidden');
            negFeed.classList.add('hidden');
            negFeed.classList.remove('active');
        } else {
            negFeed.classList.add('active');
            negFeed.classList.remove('hidden');
            posFeed.classList.add('hidden');
            posFeed.classList.remove('active');
        }
    };

    // function updateEnsembleUI(stats, transStatus) {
    //     ...
    // }
});

// ═══════════════════════════════════════════════════════════════════
// REAL-TIME TWEET STREAM ENGINE — Dashboard Integration
// Connects SSE stream → drives Main Dashboard (charts, emotions, Intel)
// ═══════════════════════════════════════════════════════════════════
const STREAM_URL = 'http://127.0.0.1:8888/stream';
const BATCH_URL  = 'http://127.0.0.1:8888/stream/batch';
const STATUS_URL = 'http://127.0.0.1:8888/stream/status';
const API_PREDICT = 'http://127.0.0.1:8888/predict';

// ── Stream state ────────────────────────────────
let streamSource     = null;
let streamPaused     = false;
const MAX_CHIPS      = 40;

// Running sentiment tally (drives live donut charts)
let livePosTotal  = 0;
let liveNegTotal  = 0;
let liveNeuTotal  = 0;
let streamTweetCount = 0;

// Throttle: trigger full dashboard update every N tweets
const DASHBOARD_UPDATE_EVERY = 5;
let lastDashboardText = '';

// ── DOM refs ────────────────────────────────────
const feedEl      = document.getElementById('liveStreamFeed');
const statusBadge = document.getElementById('streamStatus');
const toggleBtn   = document.getElementById('toggleStream');
const statSource  = document.getElementById('streamSource');

const statTotal   = document.getElementById('streamTotal');
const statPos     = document.getElementById('streamPos');
const statNeg     = document.getElementById('streamNeg');

// ── 1. Create a clean tweet chip (NO sentiment label) ────────────
function createChip(tweet) {
    const chip = document.createElement('div');
    // Use left-border color based on sentiment but show NO badge text
    let borderColor = '#94a3b8'; // neutral grey
    if (tweet.sentiment === 'Positive') borderColor = '#10b981';
    if (tweet.sentiment === 'Negative') borderColor = '#ef4444';
    chip.className = 'tweet-chip';
    chip.style.borderLeft = '3px solid ' + borderColor;

    const srcLabel = tweet.source === 'twitter_api' ? '🐦 Live'
                   : tweet.source === 'nitter'      ? '🌐 Web' : '🎭 Stream';

    const rawText  = (tweet.tweet_text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const hashtags = (tweet.hashtags || []).slice(0, 3).map(h => `<span style="color:#3b82f6;font-size:0.7rem">#${h}</span>`).join(' ');
    const metrics  = tweet.public_metrics || {};
    const likes    = metrics.like_count    || 0;
    const rts      = metrics.retweet_count || 0;

    chip.innerHTML =
        '<div class="chip-source">' + srcLabel + '</div>' +
        '<div class="chip-text">'   + rawText  + '</div>' +
        (hashtags ? '<div style="margin:3px 0 4px;">' + hashtags + '</div>' : '') +
        '<div class="chip-meta">' +
            '<span>@' + (tweet.author_id || 'user') + '</span>' +
            '<span style="font-size:0.65rem;opacity:0.5">❤ ' + likes + ' · 🔁 ' + rts + '</span>' +
        '</div>';
    return chip;
}

// ── 2. Update live donut charts from running totals ──────────────
function updateLiveCharts() {
    const total = livePosTotal + liveNegTotal + liveNeuTotal || 1;
    const posP  = Math.round((livePosTotal / total) * 100);
    const negP  = Math.round((liveNegTotal / total) * 100);
    const neuP  = 100 - posP - negP;

    if (window._posChart) {
        window._posChart.data.datasets[0].data = [posP, 100 - posP];
        window._posChart.update('none');
    }
    if (window._neuChart) {
        window._neuChart.data.datasets[0].data = [neuP, 100 - neuP];
        window._neuChart.update('none');
    }
    if (window._negChart) {
        window._negChart.data.datasets[0].data = [negP, 100 - negP];
        window._negChart.update('none');
    }

    // Update live % labels under charts
    const posLbl = document.getElementById('livePosPercent');
    const neuLbl = document.getElementById('liveNeuPercent');
    const negLbl = document.getElementById('liveNegPercent');
    if (posLbl) posLbl.textContent = posP + '%';
    if (neuLbl) neuLbl.textContent = neuP + '%';
    if (negLbl) negLbl.textContent = negP + '%';

    // Show stream mode indicator
    const streamModeEl = document.getElementById('streamModeIndicator');
    if (streamModeEl) streamModeEl.style.display = 'inline-flex';

    // Update stat counters
    if (statTotal) statTotal.textContent = streamTweetCount;
    if (statPos)   statPos.textContent   = livePosTotal;
    if (statNeg)   statNeg.textContent   = liveNegTotal;
}

// ── 3. Full dashboard update from /predict ───────────────────────
async function triggerFullDashboardUpdate(tweet) {
    if (!tweet || !tweet.tweet_text || tweet.tweet_text.length < 5) return;
    const text = tweet.tweet_text;
    if (text === lastDashboardText) return;
    lastDashboardText = text;

    try {
        const resp = await fetch(API_PREDICT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        if (!resp.ok) return;
        const data = await resp.json();

        // ── Update Intelligence Report ──
        const summaryEl = document.getElementById('summaryText');
        if (summaryEl) summaryEl.innerText = data.summary;

        // ── Update Fake Detection ──
        const fakeStatusEl   = document.getElementById('fakeStatus');
        const fakeProgressEl = document.getElementById('fakeProgress');
        if (fakeStatusEl) {
            fakeStatusEl.innerText = data.fake.status;
            fakeStatusEl.style.color = data.fake.status === 'ORIGINAL' ? '#3b82f6' : '#ef4444';
        }
        if (fakeProgressEl) fakeProgressEl.style.width = data.fake.prob + '%';

        // ── Update Emotion ──
        const emotionIconEl  = document.getElementById('emotionIcon');
        const emotionLabelEl = document.getElementById('emotionLabel');
        if (emotionIconEl)  emotionIconEl.innerText  = data.emotion.icon;
        if (emotionLabelEl) emotionLabelEl.innerText = data.emotion.label;

        // ── Update Action Recommendation ──
        const recEl = document.getElementById('recommendationContent');
        if (recEl && data.recommendation) {
            const rec = data.recommendation;
            const recTitle = typeof rec === 'object' ? (rec.title || '') : rec;
            const recType  = typeof rec === 'object' ? (rec.type  || '') : '';
            const recUrl   = typeof rec === 'object' ? (rec.url   || '#') : '#';
            const recDesc  = typeof rec === 'object' && rec.description ? rec.description : (data.description || '');
            recEl.innerHTML =
                '<div class="rec-tag">' + data.mood + '</div>' +
                (recType ? '<span style="font-size:0.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;">' + recType + '</span><br>' : '') +
                '<h4 style="margin:4px 0 6px;">' + recTitle + '</h4>' +
                '<p>' + recDesc + '</p>' +
                '<a href="' + recUrl + '" target="_blank" class="rec-link">Launch Content →</a>';
        }


        // ── Update Product Intel ──
        const intelPanel = document.getElementById('productIntel');
        if (data.product_intel && intelPanel) {
            intelPanel.classList.remove('hidden');
            const issueEl  = document.getElementById('productIssue');
            const altEl    = document.getElementById('altProduct');
            const reasonEl = document.getElementById('altReason');
            if (issueEl)  issueEl.innerText  = 'Detected negative trend for ' + data.product_intel.target + '.';
            if (altEl)    altEl.innerText     = data.product_intel.alternative;
            if (reasonEl) reasonEl.innerText  = data.product_intel.suggestion;
        } else if (intelPanel) {
            intelPanel.classList.add('hidden');
        }

        // ── Update Company/Hashtag Pills ──
        const companyListEl = document.getElementById('companyList');
        if (companyListEl && data.hashtags && data.hashtags.length > 0) {
            companyListEl.innerHTML = data.hashtags
                .map(h => '<span class="pill">#' + h + '</span>')
                .join('');
        }

        // ── Feed the Review Navigator with this live tweet ──
        const feedText = '"' + (text.length > 55 ? text.substring(0, 52) + '...' : text) + '"';
        const feedItem = '<div class="feed-item new-entry">' + feedText + '</div>';
        const posFeedEl = document.getElementById('posFeed');
        const negFeedEl = document.getElementById('negFeed');
        if (data.probs.pos >= data.probs.neg) {
            if (posFeedEl) {
                posFeedEl.insertAdjacentHTML('afterbegin', feedItem);
                if (posFeedEl.children.length > 8) posFeedEl.lastElementChild.remove();
            }
        } else {
            if (negFeedEl) {
                negFeedEl.insertAdjacentHTML('afterbegin', feedItem);
                if (negFeedEl.children.length > 8) negFeedEl.lastElementChild.remove();
            }
        }

        // Mark dashboard as stream-driven
        const streamModeEl = document.getElementById('streamModeIndicator');
        if (streamModeEl) streamModeEl.style.display = 'inline-flex';

    } catch(e) {
        console.warn('Stream dashboard update failed:', e);
    }
}

// ── 4. Process each incoming tweet ───────────────────────────────
function processStreamTweet(tweet) {
    if (!tweet || !tweet.tweet_text) return;

    // Add chip to ticker without sentiment badge
    if (feedEl && !streamPaused) {
        const placeholder = feedEl.querySelector('.ticker-placeholder');
        if (placeholder) placeholder.remove();
        const chip = createChip(tweet);
        feedEl.prepend(chip);
        while (feedEl.children.length > MAX_CHIPS) feedEl.removeChild(feedEl.lastChild);
    }

    // Tally sentiment for live chart update
    if (tweet.sentiment === 'Positive') livePosTotal++;
    else if (tweet.sentiment === 'Negative') liveNegTotal++;
    else liveNeuTotal++;

    streamTweetCount++;

    // Update source badge in Stream Monitor
    if (statSource) {
        const src = tweet.source;
        statSource.className  = src === 'twitter_api' ? 'badge-real' : src === 'nitter' ? 'badge-nitter' : 'badge-mock';
        statSource.textContent = src === 'twitter_api' ? 'TWITTER' : src === 'nitter' ? 'NITTER' : 'MOCK';
    }

    // Update live donut charts on every tweet
    updateLiveCharts();

    // Every N tweets → full dashboard update (Intelligence Report, Emotion, Recommendation)
    if (streamTweetCount % DASHBOARD_UPDATE_EVERY === 0) {
        triggerFullDashboardUpdate(tweet);
    }
}

// ── 5. SSE Connection ────────────────────────────────────────────
function startSSEStream() {
    if (streamSource) streamSource.close();
    streamSource = new EventSource(STREAM_URL);
    if (statusBadge) { statusBadge.textContent = 'LIVE'; statusBadge.classList.remove('paused'); }

    streamSource.onmessage = function(e) {
        if (streamPaused) return;
        try {
            const data = JSON.parse(e.data);
            if (data.heartbeat) return;
            processStreamTweet(data);
        } catch(_) {}
    };

    streamSource.onerror = function() {
        if (statusBadge) statusBadge.textContent = 'RECONNECTING...';
        setTimeout(pollBatchFallback, 2000);
    };
}

function pollBatchFallback() {
    fetch(BATCH_URL + '?count=5')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            (data.tweets || []).forEach(function(t) { processStreamTweet(t); });
            if (statusBadge) { statusBadge.textContent = 'LIVE (POLL)'; statusBadge.classList.remove('paused'); }
        })
        .catch(function() { if (statusBadge) statusBadge.textContent = 'OFFLINE'; });
}


// ── 7. Pause / Resume toggle ─────────────────────────────────────
window.toggleLiveStream = function() {
    streamPaused = !streamPaused;
    if (toggleBtn)   toggleBtn.textContent = streamPaused ? 'RESUME' : 'PAUSE';
    if (statusBadge) {
        statusBadge.textContent = streamPaused ? 'PAUSED' : 'LIVE';
        statusBadge.classList.toggle('paused', streamPaused);
    }
};

// ── 8. Auto-start ────────────────────────────────────────────────
if (typeof EventSource !== 'undefined') {
    startSSEStream();
} else {
    setInterval(pollBatchFallback, 4000);
    pollBatchFallback();
}
