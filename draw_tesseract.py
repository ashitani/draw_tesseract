import numpy as np
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import itertools
import os

# 四次元点を３次元座標に透視投影(いいかげん。u=1のときにx,y,zがscale倍される)
def project(point4d,scale=0.75):
    x,y,z,u=point4d
    s= (scale-1)*(u-1)+scale
    return [x*s,y*s,z*s]

#p0,p1のユークリッド距離
def distance(p0,p1):
    d=0
    for a,b in zip(p0,p1):
        d+=(a-b)**2
    return np.sqrt(d)

#点群pointsから距離２（最短距離）の点ペアを列挙
def get_pairs(points, target_distance=2.1):
    pairs=[]
    for p in itertools.combinations(points,2):
        d=distance(p[0],p[1])
        if(d<target_distance):
            pairs.append( [p[0],p[1]]) 
    return pairs

#頂点ペアを3Dプロット
def plot_lines(ax,pairs):
    for p in pairs:
        p[0]=project(p[0])
        p[1]=project(p[1])
        p=np.array(p)
        x=p[:,0]
        y=p[:,1]
        z=p[:,2]
        ax.plot(x,y,z,"o-b")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    # ax.set_xticks([-1,0,1])
    # ax.set_yticks([-1,0,1])
    # ax.set_zticks([-1,0,1])
    ax.set_xlim(-1.5,1.5)
    ax.set_ylim(-1.5,1.5)
    ax.set_zlim(-1.5,1.5)
    plt.axis('off')
    return

# xu,yu,zu平面での回転
# https://mixedmoss.com/4dimensionGeometry/8-cells/developement%20of%20super%20cube.pdf
def rotate(point, plane, theta_degree):
    t=[]
    X=[1,0,0,0]
    Y=[0,1,0,0]
    Z=[0,0,1,0]
    U=[0,0,0,1]
    if(plane=="xy"):
        t=[X,Y,Z,U]
    elif(plane=="yz"):
        t=[Y,Z,X,U]
    elif(plane=="xz"):
        t=[X,Z,Y,U]
    elif(plane=="xu"):
        t=[X,U,Y,Z]
    elif(plane=="yu"):
        t=[Y,U,X,Z]
    elif(plane=="zu"):
        t=[Z,U,X,Y]
    else:
        print("unknown plane:"+plane)
        exit(-1)
    t=np.matrix(t)

    theta = theta_degree/180*np.pi
    mat=np.matrix([
        [np.cos(theta), -np.sin(theta),0,0 ],
        [np.sin(theta), np.cos(theta),0,0 ],
        [0,0,1,0],
        [0,0,0,1]        
    ])
    point=np.matrix(point).reshape(4,1)
    rotated_point=t.T*mat*t*point
    rotated_point =rotated_point.reshape(1,4).tolist()[0]
    return rotated_point

# 超立方体を作成し、指定したplaneでangle[deg]回転させる
# planesは文字列のリストで、平面はxyzuのうち２文字を指定
# 複数指定すると同じ角度で複数平面回転を行う。
# planes=["xy"]       xy平面でangle回転
# planes=["xu","yu"]  xu平面、yu平面でangleずつ回転
def plot_tesseract(ax,planes, angle):
    # 超立方体の頂点を作成しつつ回転させる
    dimensions=4
    points=[]
    for x in itertools.product([1,-1],repeat=dimensions):
        p=x
        for plane in planes:
            p=rotate(p,plane,angle)
        points.append(p)

    # 距離が２（最も近い距離）の頂点ペアを列挙する
    pairs=get_pairs(points)

    # 描画
    plot_lines(ax,pairs)

if __name__ == "__main__":
    
    angle_step=1 #1フレームあたりの角度ステップ
    frames=int(180/angle_step)

    fig = plt.figure(figsize=plt.figaspect(1))
    def update(i):
        plt.clf()
        angle=i*angle_step
        print("\r%d/180"%angle,end="")
        ax = fig.add_subplot(111, projection='3d')
#        plot_tesseract(ax,["xu","yu","zu"],angle)
        plot_tesseract(ax,["xu"],angle)

    ani = animation.FuncAnimation(fig, update, frames=frames, interval = 30)
    ani.save('tesseract.mp4')

    conv="ffmpeg -y -i tesseract.mp4 -r 30 -loop 0 -f gif tesseract.gif"
    os.system(conv)
