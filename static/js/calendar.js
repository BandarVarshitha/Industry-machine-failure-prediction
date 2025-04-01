class Calendar {
    constructor(element, options) {
        this.element = element;
        this.options = options;
        this.events = options.events || [];
        this.headerToolbar = options.headerToolbar || {};
        this.currentMonth = new Date().getMonth();
        this.currentYear = new Date().getFullYear();
    }

    render() {
        this.element.innerHTML = `
            <div style="color: white; text-align: center; margin-bottom: 20px;">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <button class="btn btn-primary" id="prevMonth">Previous</button>
                    <h4>${this.getMonthName(this.currentMonth)} ${this.currentYear}</h4>
                    <button class="btn btn-primary" id="nextMonth">Next</button>
                </div>
                <div id="calendarMonth" style="border: 1px solid #ccc; border-radius: 10px; background-color: #1e293b; padding: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);">
                    ${this.renderMonth(this.currentYear, this.currentMonth)}
                </div>
            </div>
        `;

        this.addEventListeners();
    }

    renderMonth(year, month) {
        const monthNames = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ];
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        let monthHTML = `
            <div class="month-grid" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; text-align: center; font-size: 12px;">
                <div style="font-weight: bold; color: #a0aec0;">Sun</div>
                <div style="font-weight: bold; color: #a0aec0;">Mon</div>
                <div style="font-weight: bold; color: #a0aec0;">Tue</div>
                <div style="font-weight: bold; color: #a0aec0;">Wed</div>
                <div style="font-weight: bold; color: #a0aec0;">Thu</div>
                <div style="font-weight: bold; color: #a0aec0;">Fri</div>
                <div style="font-weight: bold; color: #a0aec0;">Sat</div>
        `;

        // Add empty cells for days before the first day of the month
        for (let i = 0; i < firstDay; i++) {
            monthHTML += `<div style="height: 30px; border: 1px solid #4a5568; background-color: #1a202c;"></div>`;
        }

        // Add days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day).toISOString().split('T')[0];
            const event = this.events.find(event => event.start === date);

            monthHTML += `
                <div 
                    class="calendar-day" 
                    data-date="${date}" 
                    style="height: 30px; border: 1px solid #4a5568; background-color: ${event ? '#4CAF50' : '#2d3748'}; color: white; position: relative; display: flex; align-items: center; justify-content: center; border-radius: 3px; cursor: ${event ? 'pointer' : 'default'};">
                    <span style="font-weight: bold;">${day}</span>
                </div>
            `;
        }

        monthHTML += `</div>`;
        return monthHTML;
    }

    addEventListeners() {
        const prevButton = this.element.querySelector('#prevMonth');
        const nextButton = this.element.querySelector('#nextMonth');

        prevButton.addEventListener('click', () => {
            this.currentMonth--;
            if (this.currentMonth < 0) {
                this.currentMonth = 11;
                this.currentYear--;
            }
            this.render();
        });

        nextButton.addEventListener('click', () => {
            this.currentMonth++;
            if (this.currentMonth > 11) {
                this.currentMonth = 0;
                this.currentYear++;
            }
            this.render();
        });

        const days = this.element.querySelectorAll('.calendar-day[data-date]');
        days.forEach(day => {
            day.addEventListener('click', (e) => {
                const date = e.currentTarget.getAttribute('data-date');
                const event = this.events.find(event => event.start === date);
                if (event) {
                    this.showEventDetails(event);
                }
            });
        });
    }

    showEventDetails(event) {
        const modal = document.getElementById('eventModal');
        const modalTitle = modal.querySelector('.modal-title');
        const modalBody = modal.querySelector('.modal-body');

        modalTitle.textContent = `Scheduled Maintenance on ${event.start}`;
        modalBody.innerHTML = `
            <p><strong>Machine ID:</strong> ${event.machineId}</p>
            <p><strong>Maintenance Type:</strong> ${event.title}</p>
            <p><strong>Estimated Cost:</strong> $${event.cost || 'N/A'}</p>
            <p><strong>Estimated Duration:</strong> ${event.duration || 'N/A'} hours</p>
        `;

        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    getMonthName(month) {
        const monthNames = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ];
        return monthNames[month];
    }
}
