document.addEventListener('DOMContentLoaded', function() {
    // Initialize the calendar
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: ''  // Removed timeGridWeek view
        },
        eventClick: function(info) {
            // Check if the date is in the past
            const clickedDate = info.event.start;
            if (isPastDate(clickedDate)) {
                return; // Don't do anything for past dates
            }
            
            // Remove clicked class from all days
            document.querySelectorAll('.fc-daygrid-day').forEach(day => {
                day.classList.remove('clicked');
            });
            
            // Add clicked class to the clicked day
            const dateStr = formatDate(clickedDate);
            const dayEl = document.querySelector(`.fc-day[data-date="${dateStr}"]`);
            if (dayEl) {
                dayEl.classList.add('clicked');
            }
            
            fetchServiceDetails(info.event.startStr);
        },
        dateClick: function(info) {
            // Check if the date is in the past
            const clickedDate = new Date(info.dateStr);
            if (isPastDate(clickedDate)) {
                return; // Don't do anything for past dates
            }
            
            // Remove clicked class from all days
            document.querySelectorAll('.fc-daygrid-day').forEach(day => {
                day.classList.remove('clicked');
            });
            
            // Add clicked class to the clicked day
            info.dayEl.classList.add('clicked');
            
            fetchServiceDetails(info.dateStr);
        },
        eventContent: function(arg) {
            return {
                html: `<div class="service-count-badge">${arg.event.extendedProps.count}</div>`
            };
        },
        dayCellDidMount: function(info) {
            // Disable past dates
            if (isPastDate(info.date)) {
                info.el.classList.add('fc-day-disabled');
            }
        }
    });
    
    calendar.render();
    
    // Fetch prediction data and populate the calendar
    fetchPredictionData();
    
    // Set today's date in the sidebar
    const today = new Date();
    fetchServiceDetails(formatDate(today));
    
    // Function to check if a date is in the past
    function isPastDate(date) {
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Set to beginning of day for accurate comparison
        const checkDate = new Date(date);
        checkDate.setHours(0, 0, 0, 0);
        return checkDate < today;
    }
    
    // Function to fetch prediction data from the API
    function fetchPredictionData() {
        fetch('/api/predictions')
            .then(response => response.json())
            .then(data => {
                // Clear existing events
                calendar.removeAllEvents();
                
                // Add events based on prediction data
                const events = [];
                const predictionsByDate = {};
                
                // Group predictions by date
                data.predictions.forEach(prediction => {
                    const date = prediction.date;
                    if (!predictionsByDate[date]) {
                        predictionsByDate[date] = [];
                    }
                    predictionsByDate[date].push(prediction);
                });
                
                // Create events for each date
                for (const [date, predictions] of Object.entries(predictionsByDate)) {
                    events.push({
                        title: `${predictions.length} Services`,
                        start: date,
                        extendedProps: {
                            count: predictions.length
                        },
                        backgroundColor: getColorByCount(predictions.length),
                        borderColor: getColorByCount(predictions.length)
                    });
                }
                
                // Add events to calendar
                calendar.addEventSource(events);
                
                // Update overview counts
                updateOverviewCounts(data.predictions);
                
                // Highlight today's date
                const todayEl = document.querySelector('.fc-day-today');
                if (todayEl) {
                    todayEl.classList.add('clicked');
                }
                
                // Apply disabled style to past dates
                applyPastDateStyling();
            })
            .catch(error => {
                console.error('Error fetching prediction data:', error);
            });
    }
    
    // Function to apply styling to past dates
    function applyPastDateStyling() {
        document.querySelectorAll('.fc-daygrid-day').forEach(dayEl => {
            const dateStr = dayEl.getAttribute('data-date');
            if (dateStr) {
                const date = new Date(dateStr);
                if (isPastDate(date)) {
                    dayEl.classList.add('fc-day-disabled');
                }
            }
        });
    }
    
    // Function to update overview counts (today, week, month)
    function updateOverviewCounts(predictions) {
        const today = new Date();
        const todayStr = formatDate(today);
        
        // Calculate today's count
        const todayCount = predictions.filter(p => p.date === todayStr).length;
        document.getElementById('today-count').textContent = todayCount;
        
        // Calculate this week's count
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - today.getDay()); // Start of current week (Sunday)
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6); // End of current week (Saturday)
        
        const weekCount = predictions.filter(p => {
            const predDate = new Date(p.date);
            return predDate >= weekStart && predDate <= weekEnd;
        }).length;
        document.getElementById('week-count').textContent = weekCount;
        
        // Calculate this month's count
        const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        
        const monthCount = predictions.filter(p => {
            const predDate = new Date(p.date);
            return predDate >= monthStart && predDate <= monthEnd;
        }).length;
        document.getElementById('month-count').textContent = monthCount;
    }
    
    // Function to fetch service details for a specific date
    function fetchServiceDetails(date) {
        fetch(`/api/predictions/${date}`)
            .then(response => response.json())
            .then(data => {
                const detailsContainer = document.getElementById('service-details');
                
                if (data.predictions.length === 0) {
                    detailsContainer.innerHTML = `<p class="text-center text-muted">No services predicted for ${formatDateDisplay(date)}</p>`;
                    return;
                }
                
                let html = `<h6 class="mb-3">Services for ${formatDateDisplay(date)}</h6>`;
                
                data.predictions.forEach(prediction => {
                    html += `
                        <div class="customer-item">
                            <div class="phone-number">${prediction.phone_number}</div>
                            <div class="usage-info mt-1">
                                <span class="badge bg-light text-dark">
                                    <i class="fas fa-tachometer-alt"></i> ${prediction.avg_km_per_month} km/month
                                </span>
                            </div>
                            <div class="spare-parts mt-2">
                                <div class="text-muted small">Spare Parts:</div>
                    `;
                    
                    prediction.spare_parts.forEach(part => {
                        html += `
                            <div class="spare-part-item">
                                <span class="fw-medium">${part.name}</span> - ${part.reason}
                            </div>
                        `;
                    });
                    
                    html += `
                            </div>
                        </div>
                    `;
                });
                
                detailsContainer.innerHTML = html;
            })
            .catch(error => {
                console.error('Error fetching service details:', error);
            });
    }
    
    // Helper function to format date as YYYY-MM-DD
    function formatDate(date) {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // Helper function to format date for display
    function formatDateDisplay(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { 
            weekday: 'short', 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }
    
    // Helper function to get color based on count
    function getColorByCount(count) {
        if (count < 3) return '#52616b'; // Light blue-gray for low count
        if (count < 7) return '#1e2022'; // Dark blue-gray for medium count
        return '#0f4c81'; // Deep blue for high count
    }
    
    // Set up auto-refresh every 5 minutes
    setInterval(fetchPredictionData, 5 * 60 * 1000);
});
