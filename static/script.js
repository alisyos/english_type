document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('pdfFiles');
    const submitButton = document.querySelector('button[type="submit"]');
    const fileList = document.getElementById('fileList');

    // 드래그 이벤트 처리
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // 드래그 효과
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('bg-light');
    }

    function unhighlight(e) {
        dropZone.classList.remove('bg-light');
    }

    // 파일 드롭 처리
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        const files = e.dataTransfer.files;
        handleFiles(files);
        // 파일 입력 요소에 드롭된 파일 설정
        fileInput.files = files;
    });

    // 파일 선택 처리
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            fileList.innerHTML = '';
            let validFiles = true;
            
            Array.from(files).forEach(file => {
                if (file.type === 'application/pdf') {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'alert alert-info mb-2';
                    fileItem.innerHTML = `
                        <i class="bi bi-file-pdf me-2"></i>
                        ${file.name}
                    `;
                    fileList.appendChild(fileItem);
                } else {
                    validFiles = false;
                    alert('PDF 파일만 업로드 가능합니다.');
                }
            });
            
            submitButton.disabled = !validFiles;
        }
    }

    // 파일 분석 상태 업데이트 함수 수정
    function updateFileStatus(fileName, status, message = '') {
        const statusList = document.getElementById('statusList');
        let existingStatus = statusList.querySelector(`[data-file="${fileName}"]`);
        
        if (!existingStatus) {
            existingStatus = document.createElement('div');
            existingStatus.className = 'analysis-status';
            existingStatus.setAttribute('data-file', fileName);
            statusList.appendChild(existingStatus);
        }
        
        let statusText = '';
        let icon = '';
        let statusClass = '';
        
        switch(status) {
            case 'processing':
                statusText = '분석 중';
                icon = '<i class="bi bi-arrow-repeat me-2"></i>';
                statusClass = 'processing';
                break;
            case 'completed':
                statusText = '분석 완료';
                icon = '<i class="bi bi-check-circle me-2"></i>';
                statusClass = 'completed';
                break;
            case 'error':
                statusText = '분석 실패';
                icon = '<i class="bi bi-exclamation-circle me-2"></i>';
                statusClass = 'error';
                break;
        }
        
        existingStatus.className = `analysis-status ${statusClass}`;
        existingStatus.innerHTML = `
            ${icon}
            <strong>${fileName}</strong>: ${statusText}
            ${message ? `<br><small class="text-muted">${message}</small>` : ''}
        `;
    }

    // 폼 제출 처리
    document.getElementById('uploadForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const files = document.getElementById('pdfFiles').files;
        const analysisStatus = document.getElementById('analysisStatus');
        const statusList = document.getElementById('statusList');
        const result = document.getElementById('result');
        
        analysisStatus.classList.remove('d-none');
        result.classList.remove('d-none');
        statusList.innerHTML = '';
        
        const resultTableBody = document.getElementById('resultTableBody');
        resultTableBody.innerHTML = '';
        
        try {
            for (let file of files) {
                updateFileStatus(file.name, 'processing');
                
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    console.log('GPT 응답 전체 데이터:', data); // 전체 응답 데이터 출력
                    
                    if (data.error) {
                        updateFileStatus(file.name, 'error', data.error);
                    } else {
                        updateFileStatus(file.name, 'completed');
                        addResultToTable(data);
                    }
                } catch (error) {
                    updateFileStatus(file.name, 'error', error.message);
                    console.error('Error:', error);
                }
            }

            // 다운로드 버튼 활성화
            updateDownloadButton(true);

        } catch (error) {
            console.error('Error:', error);
            alert(`오류가 발생했습니다: ${error.message}`);
        }
    });
});

// 결과 테이블에 데이터 추가하는 함수
function addResultToTable(data) {
    const tableBody = document.getElementById('resultTableBody');
    const row = document.createElement('tr');
    
    row.innerHTML = `
        <td>${data.school_name || ''}</td>
        <td>${data.publisher || ''}</td>
        <td>${data.grade || ''}</td>
        <td>${data.exam_type || ''}</td>
        <td>${data.total_questions || 0}</td>
        <td>${getQuestionInfo(data.question_types, '빈칸추론')}</td>
        <td>${getQuestionInfo(data.question_types, '주제추론')}</td>
        <td>${getQuestionInfo(data.question_types, '제목추론')}</td>
        <td>${getQuestionInfo(data.question_types, '요지추론')}</td>
        <td>${getQuestionInfo(data.question_types, '필자주장')}</td>
        <td>${getQuestionInfo(data.question_types, '밑줄어휘')}</td>
        <td>${getQuestionInfo(data.question_types, '밑줄어법')}</td>
        <td>${getQuestionInfo(data.question_types, '문단요약')}</td>
        <td>${getQuestionInfo(data.question_types, '순서배열')}</td>
        <td>${getQuestionInfo(data.question_types, '문장삽입')}</td>
        <td>${getQuestionInfo(data.question_types, '문장삭제')}</td>
        <td>${getQuestionInfo(data.question_types, '영영풀이')}</td>
        <td>${getQuestionInfo(data.question_types, '지문내용')}</td>
        <td>${getQuestionInfo(data.question_types, '분위기/심경')}</td>
        <td>${getQuestionInfo(data.question_types, '목적')}</td>
        <td>${getQuestionInfo(data.question_types, '부적절한')}</td>
        <td>${getQuestionInfo(data.question_types, '알 수 없는 정보')}</td>
        <td>${getQuestionInfo(data.question_types, '답할 수 없는 질문')}</td>
        <td>${getQuestionInfo(data.question_format, 'multiple_choice')}</td>
        <td>${getQuestionInfo(data.question_format, 'subjective')}</td>
        <td>${getQuestionScopeInfo(data.question_scope, '범위_교과서')}</td>
        <td>${getQuestionScopeInfo(data.question_scope, '범위_모의고사')}</td>
        <td>${getQuestionScopeInfo(data.question_scope, '범위_부교재')}</td>
        <td>${data.total_characters || 0}</td>
        <td>${Array.isArray(data.highest_difficulty_vocab) ? data.highest_difficulty_vocab.join(', ') : ''}</td>
    `;
    
    tableBody.appendChild(row);
}

function getQuestionInfo(questionTypes, type) {
    if (!questionTypes || !questionTypes[type]) return '0';
    const count = questionTypes[type].count || 0;
    const numbers = questionTypes[type].numbers || [];
    return `${count} (${numbers.join(', ')})`;
}

function updateDownloadButton(enabled = true) {
    const button = document.getElementById('downloadExcel');
    button.disabled = !enabled;
    button.classList.toggle('btn-success', enabled);
    button.classList.toggle('btn-secondary', !enabled);
}

// 엑셀 다운로드 함수 수정
function downloadExcel() {
    const table = document.getElementById('resultTableBody');
    const rows = table.getElementsByTagName('tr');
    const wb = XLSX.utils.book_new();
    
    // 헤더 정의 수정
    const headers = [
        "학교명", "출판사", "학년", "시험종류", "총문항수",
        "빈칸추론", "주제추론", "제목추론", "요지추론", "필자주장",
        "밑줄어휘", "밑줄어법", "문단요약", "순서배열", "문장삽입",
        "문장삭제", "영영풀이", "지문내용", "분위기/심경", "목적",
        "부적절한", "알 수 없는 정보", "답할 수 없는 질문",
        "객관식", "서술형",
        "교과서 범위", "모의고사 범위", "부교재 범위",
        "총글자수", "어려운어휘"
    ];

    // 데이터 배열 생성
    const data = [headers];
    for (let i = 0; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        const rowData = [];
        for (let j = 0; j < cells.length; j++) {
            rowData.push(cells[j].textContent);
        }
        data.push(rowData);
    }

    // 워크시트 생성
    const ws = XLSX.utils.aoa_to_sheet(data);
    
    // 컬럼 너비 설정
    const colWidths = headers.map(header => ({wch: 15}));
    ws['!cols'] = colWidths;

    // 워크북에 시트 추가
    XLSX.utils.book_append_sheet(wb, ws, "분석결과");

    // 파일 다운로드
    XLSX.writeFile(wb, "영어시험지_분석결과.xlsx");
}

// 다운로드 버튼 이벤트 리스너
document.getElementById('downloadExcel').addEventListener('click', downloadExcel);

// 범위 정보를 표시하기 위한 새로운 함수 추가
function getQuestionScopeInfo(scope, type) {
    if (!scope || !scope[type]) return '0';
    const count = scope[type].count || 0;
    const numbers = scope[type].numbers || [];
    const chapters = scope[type].chapters || [];
    return `${count} (${numbers.join(', ')}) [${chapters.join(', ')}]`;
} 