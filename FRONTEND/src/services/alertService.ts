import Swal from 'sweetalert2'

export interface ReceivePaymentPromptResult {
  valorRecebido: number
  juros: number | null
}

export interface ReceiptChoicePromptItem {
  id: number
  title: string
  description: string
}

const sharedClasses = {
  popup: 'swal-popup',
  title: 'swal-title',
  htmlContainer: 'swal-text',
  confirmButton: 'swal-button',
  cancelButton: 'swal-button swal-button--ghost',
}

const confirmCancelClasses = {
  ...sharedClasses,
  actions: 'swal-actions swal-actions--spaced',
  confirmButton: 'swal-button swal-button--success-soft swal-button--with-icon',
  cancelButton: 'swal-button swal-button--danger-soft swal-button--with-icon',
}

export async function confirmDeleteAlert(): Promise<boolean> {
  const result = await Swal.fire({
    title: 'Excluir cadastro?',
    text: 'Essa acao remove o registro da lista.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Excluir',
    cancelButtonText: 'Cancelar',
    reverseButtons: true,
    buttonsStyling: false,
    customClass: sharedClasses,
    background: '#fffaf9',
    color: '#24303b',
    confirmButtonColor: '#d84b62',
  })

  return result.isConfirmed
}

export async function confirmActionAlert(title: string, text: string, confirmButtonText = 'Confirmar'): Promise<boolean> {
  const result = await Swal.fire({
    title,
    text,
    icon: 'question',
    showCancelButton: true,
    confirmButtonText: buildSwalButtonLabel(confirmButtonText, 'confirm'),
    cancelButtonText: buildSwalButtonLabel('Cancelar', 'cancel'),
    reverseButtons: true,
    buttonsStyling: false,
    customClass: confirmCancelClasses,
    background: '#fffaf9',
    color: '#24303b',
  })

  return result.isConfirmed
}

export async function receivePaymentPrompt(initialValue: number | null): Promise<ReceivePaymentPromptResult | null> {
  const defaultValue = initialValue === null ? '' : formatDecimalInput(initialValue)
  const defaultInterest = '0,00'

  const result = await Swal.fire({
    title: 'Receber parcela',
    html: `
      <div class="swal-form-grid">
        <label class="swal-form-field">
          <span>Valor recebido</span>
          <input id="swal-valor-recebido" class="swal2-input" value="${defaultValue}" />
        </label>
        <label class="swal-form-field">
          <span>Juros</span>
          <input id="swal-juros" class="swal2-input" value="${defaultInterest}" readonly />
        </label>
      </div>
    `,
    showCancelButton: true,
    confirmButtonText: buildSwalButtonLabel('Receber', 'confirm'),
    cancelButtonText: buildSwalButtonLabel('Cancelar', 'cancel'),
    reverseButtons: true,
    buttonsStyling: false,
    customClass: confirmCancelClasses,
    background: '#fffaf9',
    color: '#24303b',
    focusConfirm: false,
    didOpen: () => {
      const valueInput = document.getElementById('swal-valor-recebido') as HTMLInputElement | null
      const interestInput = document.getElementById('swal-juros') as HTMLInputElement | null

      const syncInterest = () => {
        if (!interestInput) {
          return
        }

        const paidValue = parseDecimalInput(valueInput?.value)
        const baseValue = initialValue ?? 0
        const interestValue = paidValue === null ? 0 : Math.max(paidValue - baseValue, 0)
        interestInput.value = formatDecimalInput(interestValue)
      }

      valueInput?.addEventListener('input', syncInterest)
      syncInterest()
    },
    preConfirm: () => {
      const valorRecebido = parseDecimalInput((document.getElementById('swal-valor-recebido') as HTMLInputElement | null)?.value)
      const juros = parseDecimalInput((document.getElementById('swal-juros') as HTMLInputElement | null)?.value)

      if (valorRecebido === null || valorRecebido <= 0) {
        Swal.showValidationMessage('Informe um valor recebido maior que zero.')
        return undefined
      }

      return {
        valorRecebido,
        juros,
      }
    },
  })

  return result.isConfirmed ? (result.value as ReceivePaymentPromptResult) : null
}

export async function successAlert(message: string, tone: 'create' | 'update' | 'delete' = 'create'): Promise<void> {
  const colorMap = {
    create: '#1f9d68',
    update: '#2f6fec',
    delete: '#d84b62',
  } as const

  const backgroundMap = {
    create: '#f3fcf7',
    update: '#f4f8ff',
    delete: '#fff7f8',
  } as const

  await Swal.fire({
    title: message,
    icon: 'success',
    timer: 1800,
    showConfirmButton: false,
    toast: true,
    position: 'top-end',
    background: backgroundMap[tone],
    color: colorMap[tone],
  })
}

export async function errorAlert(message: string): Promise<void> {
  await Swal.fire({
    title: 'Operacao nao concluida',
    text: message,
    icon: 'error',
    confirmButtonText: 'Fechar',
    buttonsStyling: false,
    customClass: sharedClasses,
    background: '#fff8f8',
    color: '#b63f52',
  })
}

export async function infoAlert(message: string): Promise<void> {
  await Swal.fire({
    title: 'Importante',
    text: message,
    icon: 'info',
    confirmButtonText: 'Fechar',
    buttonsStyling: false,
    customClass: sharedClasses,
    background: '#fffaf5',
    color: '#c86718',
  })
}

export async function chatMessageToast(senderName: string, message: string): Promise<void> {
  await Swal.fire({
    title: senderName,
    text: message,
    toast: true,
    position: 'top-end',
    timer: 3200,
    showConfirmButton: false,
    icon: 'info',
    background: '#fffaf5',
    color: '#c86718',
  })
}

function parseDecimalInput(value: string | undefined): number | null {
  const trimmed = (value ?? '').trim()
  if (!trimmed) {
    return null
  }

  const normalized = trimmed.replace(/\./g, '').replace(',', '.')
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function formatDecimalInput(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function buildSwalButtonLabel(label: string, tone: 'confirm' | 'cancel'): string {
  const iconPath = tone === 'confirm'
    ? 'M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'
    : 'M18.3 5.71 12 12l6.3 6.29-1.41 1.41L10.59 13.41 4.29 19.7 2.88 18.29 9.17 12 2.88 5.71 4.29 4.29l6.3 6.3 6.29-6.3z'

  return `
    <span class="swal-button__content">
      <span class="swal-button__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="${iconPath}" fill="currentColor" />
        </svg>
      </span>
      <span>${label}</span>
    </span>
  `
}

export async function chooseReceiptToDeletePrompt(items: ReceiptChoicePromptItem[]): Promise<number[] | null> {
  const result = await Swal.fire({
    title: 'Excluir pagamento',
    html: `
      <div class="swal-choice-list">
        ${items
          .map(
            (item) => `
              <label class="swal-choice-item">
                <input type="checkbox" name="receipt-choice" value="${item.id}" />
                <span class="swal-choice-item__body">
                  <strong>${item.title}</strong>
                  <small>${item.description}</small>
                </span>
              </label>
            `,
          )
          .join('')}
      </div>
    `,
    showCancelButton: true,
    confirmButtonText: buildSwalButtonLabel('Excluir', 'confirm'),
    cancelButtonText: buildSwalButtonLabel('Cancelar', 'cancel'),
    reverseButtons: true,
    buttonsStyling: false,
    customClass: confirmCancelClasses,
    background: '#fffaf9',
    color: '#24303b',
    preConfirm: () => {
      const selected = Array.from(document.querySelectorAll<HTMLInputElement>('input[name="receipt-choice"]:checked'))
      if (selected.length === 0) {
        Swal.showValidationMessage('Selecione ao menos um pagamento para excluir.')
        return undefined
      }
      return selected.map((input) => Number(input.value))
    },
  })

  return result.isConfirmed ? (result.value as number[]) : null
}