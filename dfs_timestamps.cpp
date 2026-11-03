// DFS Timestamps (tin / tout) — implementación propia, sin librerías de grafos.
//
// Convención: t arranca en 0 y SOLO aumenta al descubrir un nodo.
//   tin[v]  = valor de t al descubrir v
//   tout[v] = último tin asignado dentro del subárbol de v  (= t - 1 al salir)
// => el subárbol de v ocupa exactamente los tiempos [tin[v], tout[v]]
// => u es ancestro de v  <=>  tin[u] <= tin[v]  &&  tout[v] <= tout[u]
//
// Entrada (stdin):
//   n root q
//   n-1 líneas "a b"   (aristas no dirigidas de un árbol)
//   q líneas "u v"     (consultas: ¿u es ancestro de v?)
// Salida (stdout): traza que consume render.py
//   ENTER v padre tin     EXIT v tout     QUERY u v respuesta(0/1)
//
// Compilar: g++ -O2 -std=c++17 dfs_timestamps.cpp -o dfs_timestamps

#include <cstdio>
#include <vector>
using namespace std;

struct DfsTimestamps {
    int n, timer = 0;
    vector<vector<int>> adj;        // lista de adyacencia
    vector<int> tin, tout, parent;  // timestamps y padre

    explicit DfsTimestamps(int n) : n(n), adj(n), tin(n, -1), tout(n, -1), parent(n, -1) {}

    void addEdge(int a, int b) {
        adj[a].push_back(b);
        adj[b].push_back(a);
    }

    // DFS iterativo (pila explícita) para no depender de la recursión del sistema.
    // Costo: cada nodo se apila una vez y cada arista se mira 2 veces => O(n).
    void run(int root, bool trace) {
        vector<int> stk;            // pila de nodos "abiertos"
        vector<size_t> next(n, 0);  // próximo vecino a explorar de cada nodo
        parent[root] = -1;
        tin[root] = timer++;
        stk.push_back(root);
        if (trace) printf("ENTER %d %d %d\n", root, -1, tin[root]);
        while (!stk.empty()) {
            int v = stk.back();
            if (next[v] < adj[v].size()) {
                int u = adj[v][next[v]++];
                if (u == parent[v]) continue;  // no volver por la arista del padre
                parent[u] = v;
                tin[u] = timer++;              // descubrimiento
                stk.push_back(u);
                if (trace) printf("ENTER %d %d %d\n", u, v, tin[u]);
            } else {
                tout[v] = timer - 1;           // terminó todo su subárbol
                stk.pop_back();
                if (trace) printf("EXIT %d %d\n", v, tout[v]);
            }
        }
    }

    // O(1): solo compara dos intervalos.
    bool isAncestor(int u, int v) const { return tin[u] <= tin[v] && tout[v] <= tout[u]; }
};

int main() {
    int n, root, q;
    if (scanf("%d %d %d", &n, &root, &q) != 3) return 1;
    DfsTimestamps g(n);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        if (scanf("%d %d", &a, &b) != 2) return 1;
        g.addEdge(a, b);
    }
    g.run(root, true);
    while (q--) {
        int u, v;
        if (scanf("%d %d", &u, &v) != 2) return 1;
        printf("QUERY %d %d %d\n", u, v, g.isAncestor(u, v) ? 1 : 0);
    }
    return 0;
}
