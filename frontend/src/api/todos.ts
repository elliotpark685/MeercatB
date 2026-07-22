import { apiClient } from './client';

export interface Todo {
  id: number;
  title: string;
  description: string | null;
  due_date: string | null;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface TodoPayload {
  title: string;
  description?: string | null;
  due_date?: string | null;
  is_completed?: boolean;
}

export async function getTodos(fromDate?: string, toDate?: string): Promise<Todo[]> {
  const response = await apiClient.get('/api/v1/todos', { params: { from_date: fromDate, to_date: toDate } });
  return response.data;
}
export async function createTodo(payload: TodoPayload): Promise<Todo> {
  const response = await apiClient.post('/api/v1/todos', payload);
  return response.data;
}
export async function updateTodo(id: number, payload: Partial<TodoPayload>): Promise<Todo> {
  const response = await apiClient.patch(`/api/v1/todos/${id}`, payload);
  return response.data;
}
export async function deleteTodo(id: number): Promise<void> { await apiClient.delete(`/api/v1/todos/${id}`); }
