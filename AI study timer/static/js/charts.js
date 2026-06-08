document.addEventListener('DOMContentLoaded', () => {
    const progressChartEl = document.getElementById('progressChart');
    if (!progressChartEl) return; // Not on progress page
    
    // Fetch data from API
    fetch('/api/progress_data')
        .then(response => response.json())
        .then(data => {
            renderStudyProgressChart(data.study_dates, data.hours_scheduled, data.hours_completed);
            renderDifficultyChart(data.subjects, data.difficulties);
            renderProductivityScoreChart(data.productivity_dates, data.productivity_scores);
        })
        .catch(err => {
            console.error("Error loading charts data:", err);
            // Render placeholder empty state charts
            renderStudyProgressChart([], [], []);
            renderDifficultyChart(['Maths', 'Physics', 'Chemistry', 'AI & Robotics', 'English', 'P.E.'], [5,5,5,5,5,5]);
            renderProductivityScoreChart([], []);
        });
        
    function renderStudyProgressChart(dates, scheduled, completed) {
        const ctx = document.getElementById('progressChart').getContext('2d');
        
        // If no data yet, show mock data guidance
        if (dates.length === 0) {
            dates = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            scheduled = [4, 4, 3, 5, 4, 3, 2];
            completed = [4.5, 3.5, 4, 4.8, 3, 0, 0]; // Visual representation
        }
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Hours Completed',
                        data: completed,
                        borderColor: '#10b981', // Emerald
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 3,
                        pointBackgroundColor: '#10b981',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Hours Scheduled',
                        data: scheduled,
                        borderColor: '#3b82f6', // Blue
                        borderDash: [5, 5],
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointBackgroundColor: '#3b82f6',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#94a3b8', font: { family: 'Inter' } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' },
                        title: { display: true, text: 'Hours', color: '#94a3b8' }
                    }
                }
            }
        });
    }
    
    function renderDifficultyChart(subjects, difficulties) {
        const ctx = document.getElementById('difficultyChart').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: subjects,
                datasets: [{
                    label: 'Difficulty Rating (1-10)',
                    data: difficulties,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.65)',  // Maths
                        'rgba(139, 92, 246, 0.65)',  // Physics
                        'rgba(245, 158, 11, 0.65)',  // Chemistry
                        'rgba(6, 182, 212, 0.65)',   // AI
                        'rgba(236, 72, 153, 0.65)',  // English
                        'rgba(16, 185, 129, 0.65)'   // PE
                    ],
                    borderColor: [
                        '#3b82f6', '#8b5cf6', '#f59e0b', '#06b6d4', '#ec4899', '#10b981'
                    ],
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' },
                        min: 0,
                        max: 10
                    }
                }
            }
        });
    }
    
    function renderProductivityScoreChart(dates, scores) {
        const ctx = document.getElementById('productivityChart').getContext('2d');
        
        if (dates.length === 0) {
            dates = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            scores = [70, 75, 78, 82, 80, 85, 88];
        }
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Productivity Index',
                    data: scores,
                    borderColor: '#8b5cf6', // Purple
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 3,
                    pointBackgroundColor: '#8b5cf6',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' },
                        min: 0,
                        max: 100
                    }
                }
            }
        });
    }
});
