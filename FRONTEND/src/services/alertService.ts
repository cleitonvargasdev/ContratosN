import Swal from 'sweetalert2'

const sharedClasses = {
  popup: 'swal-popup',
  title: 'swal-title',
  htmlContainer: 'swal-text',
  confirmButton: 'swal-button',
  cancelButton: 'swal-button swal-button--ghost',
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