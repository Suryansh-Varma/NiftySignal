import type { GetServerSideProps } from 'next'

export default function GoalRedirectPage() {
  return null
}

export const getServerSideProps: GetServerSideProps = async () => {
  return {
    redirect: {
      destination: '/goal-optimizer',
      permanent: false,
    },
  }
}
