document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('pdfFiles');
    const files = fileInput.files;
    
    if (files.length === 0) {
        alert('파일을 선택해주세요.');
        return;
    }
    
    // UI 요소 상태 변경
    const loadingSpinner = document.getElementById('loadingSpinner');
    const progressList = document.getElementById('progressList');
    const result = document.getElementById('result');
    
    loadingSpinner.classList.remove('d-none');
    result.classList.remove('d-none');
    progressList.innerHTML = ''; // 진행 상태 목록 초기화
    
    const resultTableBody = document.getElementById('resultTableBody');
    resultTableBody.innerHTML = ''; // 기존 결과 초기화
    updateDownloadButton(false);
    
    try {
        // 각 파일별 진행 상태 항목 생성
        for (let file of files) {
            const progressItem = document.createElement('div');
            progressItem.className = 'list-group-item';
            progressItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <span class="filename">${file.name}</span>
                        <span class="status text-muted ms-2">대기 중...</span>
                    </div>
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">분석중...</span>
                    </div>
                </div>
            `;
            progressList.appendChild(progressItem);
            
            const statusSpan = progressItem.querySelector('.status');
            const spinner = progressItem.querySelector('.spinner-border');
            
            // 파일 업로드 및 분석
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                statusSpan.textContent = '분석 중...';
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (!data.error) {
                    // 성공 상태 표시
                    statusSpan.textContent = '완료';
                    statusSpan.className = 'status text-success ms-2';
                    spinner.remove();
                    
                    // 결과 행 추가
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${file.name}</td>
                        <td>${data.school_name || ''}</td>
                        <td>${data.grade || ''}</td>
                        <td>${data.exam_type || ''}</td>
                        <td>${data.total_questions || 0}</td>
                        <td>${getQuestionInfo(data.question_types, '내용 이해')}</td>
                        <td>${getQuestionInfo(data.question_types, '추론')}</td>
                        <td>${getQuestionInfo(data.question_types, '함의')}</td>
                        <td>${getQuestionInfo(data.question_types, '주제 파악')}</td>
                        <td>${getQuestionInfo(data.question_types, '제목 선택')}</td>
                        <td>${getQuestionInfo(data.question_types, '요지 파악')}</td>
                        <td>${getQuestionInfo(data.question_types, '필자 주장')}</td>
                        <td>${getQuestionInfo(data.question_types, '문단 요약')}</td>
                        <td>${getQuestionInfo(data.question_types, '분위기/심경 파악')}</td>
                        <td>${getQuestionInfo(data.question_types, '목적 파악')}</td>
                        <td>${getQuestionInfo(data.question_types, '빈칸 추론')}</td>
                        <td>${getQuestionInfo(data.question_types, '연결어 선택')}</td>
                        <td>${getQuestionInfo(data.question_types, '문장 순서 배열')}</td>
                        <td>${getQuestionInfo(data.question_types, '문장 삽입')}</td>
                        <td>${getQuestionInfo(data.question_types, '문장 삭제')}</td>
                        <td>${getQuestionInfo(data.question_types, '어휘 문제')}</td>
                        <td>${getQuestionInfo(data.question_types, '어법 문제')}</td>
                        <td>${getQuestionInfo(data.question_types, '문장 완성')}</td>
                        <td>${getQuestionInfo(data.question_types, '영작')}</td>
                        <td>${getQuestionInfo(data.question_types, '진위 판별')}</td>
                        <td>${getQuestionInfo(data.question_types, '영영풀이')}</td>
                        <td>${getQuestionInfo(data.question_types, '불일치 고쳐 쓰기')}</td>
                        <td>${data.total_characters || 0}</td>
                        <td>${data.highest_difficulty_vocab?.join(', ') || ''}</td>
                    `;
                    resultTableBody.appendChild(row);
                } else {
                    // 에러 상태 표시
                    statusSpan.textContent = '오류';
                    statusSpan.className = 'status text-danger ms-2';
                    spinner.remove();
                    
                    // 에러 행 추가
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${file.name}</td>
                        <td colspan="28" class="text-danger">분석 중 오류 발생: ${data.error}</td>
                    `;
                    resultTableBody.appendChild(row);
                }
            } catch (error) {
                // 에러 상태 표시
                statusSpan.textContent = '오류';
                statusSpan.className = 'status text-danger ms-2';
                spinner.remove();
                
                console.error(`Error processing ${file.name}:`, error);
            }
        }
        
        // 모든 파일 처리 완료 후 다운로드 버튼 활성화
        if (resultTableBody.children.length > 0) {
            updateDownloadButton(true);
        }
    } catch (error) {
        alert('서버 오류가 발생했습니다.');
        console.error(error);
    }
});

function getQuestionInfo(questionTypes, type) {
    if (!questionTypes || !questionTypes[type]) return '0';
    const count = questionTypes[type].count || 0;
    const numbers = questionTypes[type].numbers || [];
    return `${count} (${numbers.join(', ')})`;
}

function updateDownloadButton(enabled = true) {
    const button = document.getElementById('downloadExcel');
    if (enabled) {
        button.disabled = false;
        button.classList.remove('btn-secondary');
        button.classList.add('btn-success');
    } else {
        button.disabled = true;
        button.classList.remove('btn-success');
        button.classList.add('btn-secondary');
    }
}

// 엑셀 다운로드 버튼 이벤트
document.getElementById('downloadExcel').addEventListener('click', function() {
    const table = document.querySelector('table');
    
    // 헤더 행 가져오기
    const headers = [];
    table.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent.trim());
    });
    
    // 데이터 행 가져오기
    const rows = [];
    table.querySelectorAll('tbody tr').forEach(tr => {
        const row = [];
        tr.querySelectorAll('td').forEach(td => {
            row.push(td.textContent.trim());
        });
        rows.push(row);
    });
    
    // 워크북 생성
    const wb = XLSX.utils.book_new();
    
    // 워크시트 생성
    const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
    
    // 열 너비 자동 조정
    const colWidths = headers.map(header => ({
        wch: Math.max(
            header.length,
            ...rows.map(row => row[headers.indexOf(header)].length)
        )
    }));
    ws['!cols'] = colWidths;
    
    // 워크북에 워크시트 추가
    XLSX.utils.book_append_sheet(wb, ws, "분석결과");
    
    // 현재 날짜와 시간을 파일명에 포함
    const now = new Date();
    const timestamp = now.getFullYear() + 
                     String(now.getMonth() + 1).padStart(2, '0') + 
                     String(now.getDate()).padStart(2, '0') + '_' +
                     String(now.getHours()).padStart(2, '0') + 
                     String(now.getMinutes()).padStart(2, '0');
    
    // 엑셀 파일 다운로드
    XLSX.writeFile(wb, `영어시험지_분석결과_${timestamp}.xlsx`);
}); 