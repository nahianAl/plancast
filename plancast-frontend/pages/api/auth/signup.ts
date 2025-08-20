import { NextApiRequest, NextApiResponse } from 'next'
import { hash } from 'bcryptjs'
// import { prisma } from '@/lib/prisma'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    const { name, email, password, company } = req.body

    if (!name || !email || !password) {
      return res.status(400).json({ message: 'Missing required fields' })
    }

    // This is a mock implementation. Replace with a real database insert.
    // const hashedPassword = await hash(password, 12)
    // const user = await prisma.user.create({
    //   data: {
    //     name,
    //     email,
    //     password: hashedPassword,
    //     company,
    //   },
    // })

    // res.status(201).json({ user })

    // For now, just return a success message
    res.status(201).json({ message: 'User created successfully' })

  } else {
    res.setHeader('Allow', ['POST'])
    res.status(405).end(`Method ${req.method} Not Allowed`)
  }
}
