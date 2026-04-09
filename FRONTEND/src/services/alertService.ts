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

const CASH_REGISTER_SOUND_PATH = '/sounds/cash.mp3'

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

export function playCashRegisterSound(): void {
  if (typeof window === 'undefined') {
    return
  }

  const audio = new Audio(CASH_REGISTER_SOUND_PATH)
  audio.preload = 'auto'

  const playPromise = audio.play()
  if (playPromise) {
    void playPromise.catch(() => {
      playSynthCashRegisterSound()
    })
    return
  }

  playSynthCashRegisterSound()
}

function playSynthCashRegisterSound(): void {
  if (typeof window === 'undefined') {
    return
  }

  const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AudioContextCtor) {
    return
  }

  const audioContext = new AudioContextCtor()
  const startTime = audioContext.currentTime + 0.01
  const masterGain = audioContext.createGain()
  masterGain.gain.value = 0.9
  masterGain.connect(audioContext.destination)

  const playTone = (frequency: number, beginAt: number, duration: number, type: OscillatorType, peak: number) => {
    const oscillator = audioContext.createOscillator()
    const gain = audioContext.createGain()

    oscillator.type = type
    oscillator.frequency.setValueAtTime(frequency, beginAt)
    oscillator.frequency.exponentialRampToValueAtTime(Math.max(frequency * 0.92, 80), beginAt + duration)

    gain.gain.setValueAtTime(0.0001, beginAt)
    gain.gain.exponentialRampToValueAtTime(peak, beginAt + 0.01)
    gain.gain.exponentialRampToValueAtTime(0.0001, beginAt + duration)

    oscillator.connect(gain)
    gain.connect(masterGain)
    oscillator.start(beginAt)
    oscillator.stop(beginAt + duration + 0.02)
  }

  const clickBuffer = audioContext.createBuffer(1, Math.max(1, Math.floor(audioContext.sampleRate * 0.02)), audioContext.sampleRate)
  const clickChannel = clickBuffer.getChannelData(0)
  for (let index = 0; index < clickChannel.length; index += 1) {
    clickChannel[index] = (Math.random() * 2 - 1) * (1 - index / clickChannel.length)
  }

  const clickSource = audioContext.createBufferSource()
  clickSource.buffer = clickBuffer
  const clickFilter = audioContext.createBiquadFilter()
  clickFilter.type = 'highpass'
  clickFilter.frequency.setValueAtTime(1800, startTime)
  const clickGain = audioContext.createGain()
  clickGain.gain.setValueAtTime(0.0001, startTime)
  clickGain.gain.exponentialRampToValueAtTime(0.16, startTime + 0.004)
  clickGain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.035)
  clickSource.connect(clickFilter)
  clickFilter.connect(clickGain)
  clickGain.connect(masterGain)

  playTone(740, startTime + 0.03, 0.08, 'square', 0.14)
  playTone(1110, startTime + 0.11, 0.12, 'square', 0.18)
  playTone(1480, startTime + 0.12, 0.16, 'triangle', 0.11)
  playTone(2220, startTime + 0.135, 0.1, 'sine', 0.07)
  clickSource.start(startTime)
  clickSource.stop(startTime + 0.03)

  window.setTimeout(() => {
    void audioContext.close().catch(() => undefined)
  }, 700)
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