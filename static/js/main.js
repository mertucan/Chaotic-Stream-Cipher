document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('cipher-form');
    const buttons = form.querySelectorAll('button[type="submit"]');
    const resultContainer = document.getElementById('result-container');
    const generateSeedBtn = document.getElementById('generate-seed-btn');
    const seedInput = form.elements.seed;

    generateSeedBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/generate-seed');
            const data = await response.json();
            if (data.seed) {
                seedInput.value = data.seed;
            }
        } catch (error) {
            displayError("Failed to generate a new seed. Please try again.");
            console.error('Error generating seed:', error);
        }
    });

    buttons.forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault();
            resultContainer.innerHTML = ''; // Clear previous results

            const text = form.elements.text.value;
            const seed = seedInput.value;
            const operation = button.value;

            if (!text || !seed) {
                displayError("Please enter both the text and the security seed.");
                return;
            }

            // Show loading spinner
            const spinner = document.createElement('div');
            spinner.className = 'spinner';
            resultContainer.appendChild(spinner);

            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text, seed, operation }),
                });

                const data = await response.json();
                resultContainer.innerHTML = ''; // Clear spinner

                if (data.error) {
                    displayError(data.error);
                } else {
                    displayResults(data.steps, data.result, data.char_details, data.table_headers);
                }

            } catch (error) {
                resultContainer.innerHTML = ''; // Clear spinner
                displayError("An unexpected error occurred. Check the console for details.");
                console.error('Error:', error);
            }
        });
    });

    function displayError(message) {
        resultContainer.innerHTML = `
            <div class="error">
                <p><strong>Error:</strong> ${message}</p>
            </div>
        `;
    }

    function displayResults(steps, finalResult, charDetails, tableHeaders) {
        const stepsContainer = document.createElement('div');
        stepsContainer.className = 'steps-container';
        resultContainer.appendChild(stepsContainer);

        let delay = 0;
        steps.forEach((step, index) => {
            setTimeout(() => {
                const stepElement = document.createElement('div');
                stepElement.className = 'step';
                stepElement.innerHTML = `<p>${step.replace(/^([^:]+:)/, '<strong>$1</strong>')}</p>`;
                stepsContainer.appendChild(stepElement);
                stepElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }, delay);
            delay += 250; 
        });

        // Create and display the details table
        if (charDetails && charDetails.length > 0 && tableHeaders) {
            setTimeout(() => {
                const tableContainer = document.createElement('div');
                tableContainer.className = 'details-table-container';

                const tableTitle = document.createElement('h3');
                tableTitle.innerText = 'Character Breakdown';
                tableContainer.appendChild(tableTitle);

                const table = document.createElement('table');
                table.className = 'details-table';

                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                headerRow.innerHTML = `
                    <th>${tableHeaders.char}</th>
                    <th>${tableHeaders.original_byte}</th>
                    <th>${tableHeaders.keystream_byte}</th>
                    <th>${tableHeaders.result_byte}</th>
                `;
                thead.appendChild(headerRow);
                table.appendChild(thead);

                const tbody = document.createElement('tbody');
                charDetails.slice(0, 256).forEach(detail => { // Limit to 256 rows to prevent browser freeze
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>'${escapeHtml(detail.char)}'</td>
                        <td>${detail.original_byte.hex} <span class="char-rep">(${escapeHtml(detail.original_byte.char)})</span></td>
                        <td>${detail.keystream_byte.hex} <span class="char-rep">(${escapeHtml(detail.keystream_byte.char)})</span></td>
                        <td>${detail.result_byte.hex} <span class="char-rep">(${escapeHtml(detail.result_byte.char)})</span></td>
                    `;
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);
                tableContainer.appendChild(table);
                resultContainer.appendChild(tableContainer);
                tableContainer.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }, delay);
            delay += 250;
        }

        // Display the final result after all steps
        setTimeout(() => {
            const resultElement = document.createElement('div');
            resultElement.className = 'result';
            resultElement.innerHTML = `
                <h3>Final Result:</h3>
                <p>${finalResult}</p>
            `;
            resultContainer.appendChild(resultElement);
            resultElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, delay);
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
